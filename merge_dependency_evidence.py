#!/usr/bin/env python3
"""
合并静态 ELF、dlopen/插件线索和样机运行时采集结果（v2.1）。

改进点：
1. runtime_evidence 中写明具体由哪个进程加载；
2. 优先读取 process_library_edges.tsv，loaded_libraries.txt 作为兜底；
3. 对旧版 plugin_evidence.json 做防御性过滤：
   - 过滤 ELF 自己引用自己的 elf-string；
   - 过滤来源 ELF 未导入 dlopen/dlmopen 的 elf-string；
   - 过滤来源 ELF 已在 DT_NEEDED 中声明的字符串；
   - 过滤 .la/.pc 构建元数据产生的 text-config 噪声；
4. 兼容新版 elf-dlopen-string 证据格式。

输出分类：
- KEEP_RUNTIME_CONFIRMED：至少一个场景实际映射或 strace 打开该库；
- KEEP_STATIC_REFERENCED：静态 ELF 分析确认可达/被引用；
- REVIEW_DYNAMIC_CANDIDATE：存在有效动态加载/插件/配置线索；
- REVIEW_UNSEEN：当前三类证据均未观察到，仅可作为进一步验证候选。
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

DYNAMIC_LIBRARY_OPEN_SYMBOLS = {"dlopen", "dlmopen"}
IGNORED_METADATA_SUFFIXES = {".la", ".pc"}


def is_shared_library_name(name: str) -> bool:
    return name.endswith(".so") or ".so." in name


def library_family(name: str) -> str:
    """将 libfoo.so、libfoo.so.1、libfoo.so.1.2 归为同一名称家族。"""
    if ".so" in name:
        return name.split(".so", 1)[0] + ".so"
    return name


def is_dynamic_loader_name(name: str) -> bool:
    return bool(
        name.startswith("ld-")
        or name.startswith("ld-linux")
        or name.startswith("ld-musl")
        or name.startswith("ld-uClibc")
    ) and ".so" in name


def resolve_rootfs_symlink(path: Path, root: Path, max_hops: int = 32) -> Path:
    """在 rootfs 内解析最终文件符号链接，避免绝对链接跳到宿主机 /lib。"""
    current = path
    seen: Set[str] = set()

    for _ in range(max_hops):
        key = str(current)
        if key in seen:
            return path
        seen.add(key)

        if not current.is_symlink():
            return current

        try:
            target = os.readlink(str(current))
        except OSError:
            return current

        if os.path.isabs(target):
            current = root / target.lstrip("/")
        else:
            current = current.parent / target
        current = Path(os.path.normpath(str(current)))

    return path


def enumerate_library_aliases(root: Path) -> Tuple[Dict[str, dict], Dict[str, str]]:
    """
    返回：
      canonical_path -> {canonical_name, paths, aliases, size}
      basename/path -> canonical_path
    """
    records: Dict[str, dict] = {}
    lookup: Dict[str, str] = {}

    for current_root, _, files in os.walk(root):
        current = Path(current_root)
        for filename in files:
            if not is_shared_library_name(filename):
                continue

            path = current / filename
            virtual_path = "/" + str(path.relative_to(root))
            resolved = resolve_rootfs_symlink(path, root)

            try:
                canonical_virtual = "/" + str(resolved.relative_to(root))
            except ValueError:
                canonical_virtual = virtual_path

            record = records.setdefault(canonical_virtual, {
                "canonical_path": canonical_virtual,
                "canonical_name": os.path.basename(canonical_virtual),
                "paths": set(),
                "aliases": set(),
                "size_bytes": 0,
            })

            record["paths"].add(virtual_path)
            if path.is_symlink():
                record["aliases"].add(filename)

            try:
                record["size_bytes"] = max(
                    record["size_bytes"], resolved.stat().st_size
                )
            except OSError:
                pass

            # 完整路径优先，basename 用于匹配 DT_NEEDED/运行时路径。
            lookup[virtual_path] = canonical_virtual
            lookup[canonical_virtual] = canonical_virtual
            lookup[filename] = canonical_virtual
            lookup[os.path.basename(canonical_virtual)] = canonical_virtual

    return records, lookup


def normalize_observed_path(
    value: str,
    root: Path,
    lookup: Dict[str, str],
) -> Optional[str]:
    value = value.strip()
    if not value:
        return None

    if value.endswith(" (deleted)"):
        value = value[:-10]

    if value in lookup:
        return lookup[value]

    basename = os.path.basename(value)
    if basename in lookup:
        return lookup[basename]

    # 如果传入的是 host rootfs 绝对路径，转成目标路径。
    try:
        path = Path(value)
        if path.is_absolute():
            relative = path.resolve().relative_to(root)
            virtual = "/" + str(relative)
            if virtual in lookup:
                return lookup[virtual]
    except (OSError, ValueError, RuntimeError):
        pass

    return None


def load_json(path: Optional[str]) -> dict:
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(path)
    return json.loads(file_path.read_text(encoding="utf-8"))


def run_readelf(arguments: List[str], file_path: Path, timeout: int = 15) -> str:
    """执行 readelf；即使返回非零，也保留 stdout 中可解析的有效结果。"""
    try:
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        result = subprocess.run(
            ["readelf"] + list(arguments) + [str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        return result.stdout or ""
    except (OSError, subprocess.SubprocessError):
        return ""


def is_elf_file(path: Path) -> bool:
    try:
        with path.open("rb") as file_obj:
            return file_obj.read(4) == b"\x7fELF"
    except OSError:
        return False


def is_elf_executable(path: Path) -> bool:
    """
    判断目标是否为 ELF 可执行文件。

    - ET_EXEC 直接视为可执行文件；
    - ET_DYN 仅在存在 PT_INTERP 时视为 PIE 可执行文件；
    - 排除常规 .so/.so.<version> 共享库文件。
    """
    if path.is_symlink() or not path.is_file():
        return False
    if is_shared_library_name(path.name):
        return False
    if not is_elf_file(path):
        return False

    header = run_readelf(["-W", "-h"], path)
    match = re.search(r"^\s*Type:\s+(\S+)", header, re.MULTILINE)
    if not match:
        return False

    elf_type = match.group(1)
    if elf_type == "EXEC":
        return True
    if elf_type != "DYN":
        return False

    program_headers = run_readelf(["-W", "-l"], path)
    return bool(
        re.search(r"\bINTERP\b", program_headers)
        or "Requesting program interpreter" in program_headers
    )


def get_readelf_needed_libraries(path: Path) -> List[str]:
    """解析 ELF 动态段中的直接 DT_NEEDED 库。"""
    dependencies: List[str] = []
    output = run_readelf(["-W", "-d"], path)
    for line in output.splitlines():
        if "(NEEDED)" not in line:
            continue
        match = re.search(r"\(NEEDED\).*?\[(.+?)\]", line)
        if match:
            dependencies.append(match.group(1))
    return list(dict.fromkeys(dependencies))


def build_readelf_needed_by_map(
    root: Path,
    lookup: Dict[str, str],
) -> Tuple[Dict[str, Set[str]], dict]:
    """
    扫描 rootfs 中所有 ELF 可执行文件，建立：

        真实库路径 -> 在 DT_NEEDED 中直接声明该库的可执行文件路径集合

    注意：这里记录的是 ELF 文件路径，不是某一时刻运行中的 PID。
    """
    needed_by: Dict[str, Set[str]] = defaultdict(set)
    unmatched: Dict[str, Set[str]] = defaultdict(set)
    scanned_executables = 0
    executables_with_needed = 0
    needed_edge_count = 0

    for current_root, _, files in os.walk(root):
        current = Path(current_root)
        for filename in files:
            path = current / filename
            if not is_elf_executable(path):
                continue

            scanned_executables += 1
            executable_virtual_path = "/" + str(path.relative_to(root))
            dependencies = get_readelf_needed_libraries(path)
            if dependencies:
                executables_with_needed += 1

            for dependency in dependencies:
                needed_edge_count += 1
                canonical = normalize_observed_path(dependency, root, lookup)
                if canonical:
                    needed_by[canonical].add(executable_virtual_path)
                else:
                    unmatched[dependency].add(executable_virtual_path)

    return needed_by, {
        "scanned_elf_executable_count": scanned_executables,
        "executables_with_needed_count": executables_with_needed,
        "direct_needed_edge_count": needed_edge_count,
        "matched_library_count": len(needed_by),
        "unmatched_needed_library_count": len(unmatched),
        "unmatched_needed_libraries": {
            name: sorted(paths) for name, paths in sorted(unmatched.items())
        },
    }


def static_referenced_libraries(report: dict) -> Dict[str, Set[str]]:
    evidence: Dict[str, Set[str]] = defaultdict(set)

    dep_report = report.get("library_dependency_report", {})
    for name in dep_report.get("reachable_libraries", []):
        evidence[name].add("static:reachable_from_executable")

    for name in dep_report.get("executable_root_libraries", []):
        evidence[name].add("static:direct_executable_needed")

    ref_stats = report.get("library_reference_stats", {})
    for item in ref_stats.get("libraries", []):
        name = item.get("library")
        if not name:
            continue
        for executable in item.get("executables", []):
            evidence[name].add("static:executable:{}".format(executable))
        for library in item.get("libraries", []):
            evidence[name].add("static:library:{}".format(library))

    return evidence


def _elf_record_index(report: dict) -> Dict[str, dict]:
    index: Dict[str, dict] = {}
    for item in report.get("elf_records", []):
        path = item.get("path")
        if path:
            index[path] = item
    return index


def plugin_evidence(report: dict) -> Tuple[Dict[str, Set[str]], dict]:
    """读取插件线索，并对新版/旧版报告统一做防御性过滤。"""
    evidence: Dict[str, Set[str]] = defaultdict(set)
    elf_index = _elf_record_index(report)

    stats = {
        "accepted_count": 0,
        "ignored_self_reference_count": 0,
        "ignored_without_dlopen_count": 0,
        "ignored_needed_duplicate_count": 0,
        "ignored_metadata_count": 0,
        "ignored_unknown_count": 0,
    }

    for library_name, refs in report.get("library_referrers", {}).items():
        target_basename = os.path.basename(library_name)

        for ref in refs:
            if ":" not in ref:
                stats["ignored_unknown_count"] += 1
                continue

            kind, source = ref.split(":", 1)
            source_basename = os.path.basename(source)

            if kind in ("elf-string", "elf-dlopen-string"):
                source_record = elf_index.get(source, {})
                source_soname = source_record.get("soname")
                self_names = {source_basename}
                if source_soname:
                    self_names.add(source_soname)

                # 过滤目标库就是来源 ELF 自己的情况。新版报告优先使用
                # source SONAME；旧版报告没有 SONAME 时，再用同库家族兜底。
                same_library_family = (
                    is_shared_library_name(source_basename)
                    and library_family(target_basename)
                    == library_family(source_basename)
                )
                if target_basename in self_names or same_library_family:
                    stats["ignored_self_reference_count"] += 1
                    continue

                if is_dynamic_loader_name(target_basename):
                    stats["ignored_needed_duplicate_count"] += 1
                    continue

                needed_libraries = set(source_record.get("needed_libraries", []))
                if target_basename in needed_libraries:
                    stats["ignored_needed_duplicate_count"] += 1
                    continue

                if kind == "elf-string":
                    # 旧版 elf-string 必须确认来源 ELF 确实导入 dlopen/dlmopen。
                    loader_symbols = set(
                        source_record.get("dynamic_loader_symbols", [])
                    )
                    if not (loader_symbols & DYNAMIC_LIBRARY_OPEN_SYMBOLS):
                        stats["ignored_without_dlopen_count"] += 1
                        continue

                evidence[target_basename].add(
                    "dynamic-hint:{}:{}".format(kind, source)
                )
                stats["accepted_count"] += 1
                continue

            if kind == "text-config":
                if Path(source).suffix.lower() in IGNORED_METADATA_SUFFIXES:
                    stats["ignored_metadata_count"] += 1
                    continue
                evidence[target_basename].add(
                    "dynamic-hint:text-config:{}".format(source)
                )
                stats["accepted_count"] += 1
                continue

            if kind == "plugin-directory":
                evidence[target_basename].add(
                    "dynamic-hint:plugin-directory:{}".format(source)
                )
                stats["accepted_count"] += 1
                continue

            # 对未来新增、明确命名的证据类型保持兼容，但不接收未知 elf-string 变体。
            if kind.startswith("elf-"):
                stats["ignored_unknown_count"] += 1
                continue

            evidence[target_basename].add("dynamic-hint:{}".format(ref))
            stats["accepted_count"] += 1

    return evidence, stats


def runtime_evidence(
    runtime_dirs: Iterable[str],
    root: Path,
    lookup: Dict[str, str],
) -> Tuple[Dict[str, Set[str]], List[dict]]:
    """
    读取运行时证据。

    优先使用 process_library_edges.tsv，记录：
        runtime:<场景>:process:<进程路径>

    loaded_libraries.txt 用于补充未能关联进程的库。
    """
    evidence: Dict[str, Set[str]] = defaultdict(set)
    sessions: List[dict] = []

    for runtime_dir in runtime_dirs:
        session = Path(runtime_dir)
        if not session.is_dir():
            raise FileNotFoundError(runtime_dir)

        meta: Dict[str, str] = {}
        meta_file = session / "meta.txt"
        if meta_file.is_file():
            for line in meta_file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    meta[key] = value

        scenario = meta.get("scenario", session.name)
        libraries_with_process: Set[str] = set()
        process_edge_count = 0
        loaded_hit_set: Set[str] = set()
        strace_hit_set: Set[str] = set()

        edge_file = session / "process_library_edges.tsv"
        if edge_file.is_file():
            for line in edge_file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                if not line.strip():
                    continue

                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue

                executable = parts[0].strip() or "[unknown]"
                library_path = parts[1].strip()
                canonical = normalize_observed_path(
                    library_path, root, lookup
                )
                if not canonical:
                    continue

                evidence[canonical].add(
                    "runtime:{}:process:{}".format(scenario, executable)
                )
                libraries_with_process.add(canonical)
                process_edge_count += 1

        loaded_file = session / "loaded_libraries.txt"
        if loaded_file.is_file():
            for line in loaded_file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                canonical = normalize_observed_path(line, root, lookup)
                if not canonical:
                    continue
                loaded_hit_set.add(canonical)

                if canonical not in libraries_with_process:
                    evidence[canonical].add(
                        "runtime:{}:process:[unknown]".format(scenario)
                    )

        opened_file = session / "opened_libraries.txt"
        if opened_file.is_file():
            for line in opened_file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                canonical = normalize_observed_path(line, root, lookup)
                if not canonical:
                    continue
                evidence[canonical].add("strace:{}".format(scenario))
                strace_hit_set.add(canonical)

        sessions.append({
            "directory": str(session.resolve()),
            "scenario": scenario,
            "normalized_runtime_hits": len(loaded_hit_set),
            "process_library_edge_hits": process_edge_count,
            "libraries_with_process_count": len(libraries_with_process),
            "strace_library_hits": len(strace_hit_set),
        })

    return evidence, sessions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rootfs")
    parser.add_argument("--static-json")
    parser.add_argument("--plugin-json")
    parser.add_argument(
        "--runtime-dir",
        action="append",
        default=[],
        help="可重复指定多个运行时采集目录",
    )
    parser.add_argument("--output-prefix", default="final_lib_report")
    args = parser.parse_args()

    root = Path(args.rootfs).resolve()
    if not root.is_dir():
        raise SystemExit("rootfs 不存在: {}".format(root))

    if shutil.which("readelf") is None:
        raise SystemExit("缺少 readelf，请先安装 binutils")

    records, lookup = enumerate_library_aliases(root)
    static_report = load_json(args.static_json)
    plugin_report = load_json(args.plugin_json)

    readelf_needed_by, readelf_scan_stats = build_readelf_needed_by_map(
        root, lookup
    )
    static_raw = static_referenced_libraries(static_report)
    plugin_raw, plugin_filter_stats = plugin_evidence(plugin_report)
    runtime_raw, sessions = runtime_evidence(args.runtime_dir, root, lookup)

    static_by_canonical: Dict[str, Set[str]] = defaultdict(set)
    for name, refs in static_raw.items():
        canonical = normalize_observed_path(name, root, lookup)
        if canonical:
            static_by_canonical[canonical].update(refs)

    # 将通用的 direct_executable_needed 补充为具体 ELF 文件路径。
    for canonical, executable_paths in readelf_needed_by.items():
        for executable_path in executable_paths:
            static_by_canonical[canonical].add(
                "static:readelf-needed-by:{}".format(executable_path)
            )

    plugin_by_canonical: Dict[str, Set[str]] = defaultdict(set)
    for name, refs in plugin_raw.items():
        canonical = normalize_observed_path(name, root, lookup)
        if canonical:
            plugin_by_canonical[canonical].update(refs)

    rows: List[dict] = []
    summary: Dict[str, int] = defaultdict(int)

    for canonical, record in sorted(records.items()):
        runtime_refs = sorted(runtime_raw.get(canonical, set()))
        static_refs = sorted(static_by_canonical.get(canonical, set()))
        dynamic_refs = sorted(plugin_by_canonical.get(canonical, set()))

        if runtime_refs:
            status = "KEEP_RUNTIME_CONFIRMED"
            reason = "至少一个样机场景实际映射或 strace 打开该库"
        elif static_refs:
            status = "KEEP_STATIC_REFERENCED"
            reason = "静态 ELF 依赖图确认可达/被引用"
        elif dynamic_refs:
            status = "REVIEW_DYNAMIC_CANDIDATE"
            reason = "存在有效 dlopen、插件目录或运行配置引用线索，但运行时尚未命中"
        else:
            status = "REVIEW_UNSEEN"
            reason = "当前静态、有效动态线索和已覆盖场景均未观察到"

        summary[status] += 1

        rows.append({
            "library": record["canonical_name"],
            "canonical_path": canonical,
            "size_bytes": record["size_bytes"],
            "all_paths": sorted(record["paths"]),
            "aliases": sorted(record["aliases"]),
            "status": status,
            "reason": reason,
            "readelf_needed_by": sorted(
                readelf_needed_by.get(canonical, set())
            ),
            "runtime_evidence": runtime_refs,
            "static_evidence": static_refs,
            "dynamic_hint_evidence": dynamic_refs,
        })

    report = {
        "schema_version": "2.1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rootfs": str(root),
        "static_json": args.static_json,
        "plugin_json": args.plugin_json,
        "runtime_sessions": sessions,
        "readelf_executable_scan_stats": readelf_scan_stats,
        "plugin_hint_filter_stats": plugin_filter_stats,
        "summary": dict(sorted(summary.items())),
        "critical_warning": (
            "REVIEW_UNSEEN 不能直接等同于可删除。只有覆盖所需产品功能、异常流程、"
            "升级/恢复/诊断场景并完成移除回归后，才能升级为删除候选。"
        ),
        "libraries": rows,
    }

    prefix = Path(args.output_prefix)
    json_path = prefix.with_suffix(".json")
    csv_path = prefix.with_suffix(".csv")
    txt_path = prefix.with_suffix(".txt")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "library",
                "canonical_path",
                "size_bytes",
                "status",
                "reason",
                "readelf_needed_by",
                "runtime_evidence",
                "static_evidence",
                "dynamic_hint_evidence",
                "all_paths",
                "aliases",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **row,
                "readelf_needed_by": " | ".join(
                    row["readelf_needed_by"]
                ),
                "runtime_evidence": " | ".join(row["runtime_evidence"]),
                "static_evidence": " | ".join(row["static_evidence"]),
                "dynamic_hint_evidence": " | ".join(
                    row["dynamic_hint_evidence"]
                ),
                "all_paths": " | ".join(row["all_paths"]),
                "aliases": " | ".join(row["aliases"]),
            })

    lines = [
        "=" * 80,
        "动态库多证据合并报告（v2.1）",
        "=" * 80,
        "rootfs: {}".format(root),
        "运行时场景数: {}".format(len(sessions)),
        "",
        "readelf 可执行文件扫描统计:",
    ]
    for key, value in sorted(readelf_scan_stats.items()):
        if key == "unmatched_needed_libraries":
            continue
        lines.append("  {}: {}".format(key, value))

    lines.extend([
        "",
        "动态线索过滤统计:",
    ])
    for key, value in sorted(plugin_filter_stats.items()):
        lines.append("  {}: {}".format(key, value))

    lines.append("")
    for key, value in sorted(summary.items()):
        lines.append("{}: {}".format(key, value))

    for status in ("REVIEW_DYNAMIC_CANDIDATE", "REVIEW_UNSEEN"):
        lines.extend(["", status, "-" * len(status)])
        selected = [row for row in rows if row["status"] == status]
        if not selected:
            lines.append("无")
        for row in selected:
            lines.append(
                "{} ({} bytes) - {}".format(
                    row["canonical_path"], row["size_bytes"], row["reason"]
                )
            )
            for evidence_item in row["dynamic_hint_evidence"]:
                lines.append("  dynamic: {}".format(evidence_item))

    lines.extend(["", "重要说明:", report["critical_warning"]])
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("JSON: {}".format(json_path.resolve()))
    print("CSV : {}".format(csv_path.resolve()))
    print("文本: {}".format(txt_path.resolve()))
    print("运行时场景数: {}".format(len(sessions)))
    print("readelf扫描可执行文件: {}".format(
        readelf_scan_stats["scanned_elf_executable_count"]
    ))
    print("readelf直接NEEDED边: {}".format(
        readelf_scan_stats["direct_needed_edge_count"]
    ))
    print("有效动态线索: {}".format(plugin_filter_stats["accepted_count"]))
    print("过滤自身引用: {}".format(
        plugin_filter_stats["ignored_self_reference_count"]
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
