# M8280 / RG258UB_GLAB / UIS8510 / v610 SDK Build System 与 BBA 3.3.0 接入机制

> 工程技术说明书  
> 当前工作树：BBA 3.3.0  
> SoC / Platform：Unisoc UIS8510 / v610  
> Board：1H10 NAND  
> Kernel：Linux 6.6  
> Flash：256 MiB SPI NAND  
> Quectel Project：RG258UB_GLAB  
> Revision：RG258UB_GLABR01A01M4G  
> 文档日期：2026-09-10

---

## 目录

- [0. 文档范围与工程基线](#ch0)
  - [0.1 文档范围](#ch0-1)
  - [0.2 当前工程基线](#ch0-2)
  - [0.3 Gold SDK 与 BBA 当前工作树](#ch0-3)
  - [0.4 证据边界](#ch0-4)
  - [0.5 与刷机指南的内容边界](#ch0-5)
- [1. SDK Build System 全局架构](#ch1)
  - [1.1 Build 输入与输出](#ch1-1)
  - [1.2 五阶段 Build 模型](#ch1-2)
  - [1.3 Gold SDK 原生顶层入口](#ch1-3)
  - [1.4 阶段接口与主要产物](#ch1-4)
  - [1.5 BBA 分阶段接入概览](#ch1-5)
- [2. Build System 核心对象与目录](#ch2)
  - [2.1 产品配置对象](#ch2-1)
  - [2.2 OpenWrt Target 层级](#ch2-2)
  - [2.3 Build Framework 主文件](#ch2-3)
  - [2.4 构建目录与输出目录](#ch2-4)
- [3. 阶段一：产品配置与构建环境](#ch3)
  - [3.1 `ql_build_config` 初始化](#ch3-1)
  - [3.2 `buildconfig()` 主流程](#ch3-2)
  - [3.3 Project / Revision / Custom 处理](#ch3-3)
  - [3.4 RG258UB_GLAB 平台映射](#ch3-4)
  - [3.5 OpenWrt 顶层配置生成](#ch3-5)
  - [3.6 Feed 初始化](#ch3-6)
  - [3.7 Host Tools 与 Cross Toolchain](#ch3-7)
  - [3.8 阶段输出](#ch3-8)
- [4. 阶段二-A：Boot 构建](#ch4)
  - [4.1 Boot Package 入口](#ch4-1)
  - [4.2 Chipram4 / SPL 构建](#ch4-2)
  - [4.3 U-Boot44 构建](#ch4-3)
  - [4.4 Boot 构建配置层级](#ch4-4)
  - [4.5 Boot 主要产物](#ch4-5)
  - [4.6 Boot Build Cache](#ch4-6)
- [5. 阶段二-B：Linux Kernel、DTS / DTB 与 boot.img](#ch5)
  - [5.1 Kernel Build 入口](#ch5-1)
  - [5.2 External Kernel Tree](#ch5-2)
  - [5.3 Kernel 配置选择](#ch5-3)
  - [5.4 Kernel `.config` 合并](#ch5-4)
  - [5.5 Kernel Image 编译](#ch5-5)
  - [5.6 Device 与 DTS 映射](#ch5-6)
  - [5.7 DTB 编译](#ch5-7)
  - [5.8 `boot.img` 组装](#ch5-8)
  - [5.9 阶段输出](#ch5-9)
- [6. 阶段二-C：Kernel Module 构建](#ch6)
  - [6.1 Kernel Module 编译层](#ch6-1)
  - [6.2 `KernelPackage` 打包层](#ch6-2)
  - [6.3 `kmod-ipt-ipset` 实例](#ch6-3)
  - [6.4 `nat46` 外置模块实例](#ch6-4)
  - [6.5 Module 安装阶段](#ch6-5)
- [7. 阶段二-D：OpenWrt Userspace Package 构建](#ch7)
  - [7.1 Package 选择](#ch7-1)
  - [7.2 Package 元数据与依赖图](#ch7-2)
  - [7.3 `BuildPackage()`](#ch7-3)
  - [7.4 Prepare / Configure / Compile](#ch7-4)
  - [7.5 `Build/InstallDev`](#ch7-5)
  - [7.6 `Package/install` 与 `.pkgdir`](#ch7-6)
  - [7.7 `STAGING_DIR_ROOT`](#ch7-7)
  - [7.8 IPK 生成](#ch7-8)
  - [7.9 qlnet 构建实例](#ch7-9)
- [8. 阶段三：SDK RootFS 组装](#ch8)
  - [8.1 Package 安装清单](#ch8-1)
  - [8.2 `make package/install`](#ch8-2)
  - [8.3 `TARGET_DIR`](#ch8-3)
  - [8.4 `prepare_rootfs`](#ch8-4)
  - [8.5 SDK `root.squashfs`](#ch8-5)
  - [8.6 SDK Native RootFS 输出](#ch8-6)
- [9. 构建目录与产物流转](#ch9)
  - [9.1 `build_dir`](#ch9-1)
  - [9.2 `staging_dir` 开发 Sysroot](#ch9-2)
  - [9.3 `STAGING_DIR_ROOT`](#ch9-3)
  - [9.4 `TARGET_DIR`](#ch9-4)
  - [9.5 `bin/packages`](#ch9-5)
  - [9.6 `bin/unisoc/temp`](#ch9-6)
  - [9.7 Release 输出](#ch9-7)
  - [9.8 Userspace ELF 文件流](#ch9-8)
- [10. 阶段四：Recovery 与整机附属物料](#ch10)
  - [10.1 Recovery Image 配置](#ch10-1)
  - [10.2 Recovery RootFS 组装](#ch10-2)
  - [10.3 Recovery Package Set](#ch10-3)
  - [10.4 `recovery.squashfs`](#ch10-4)
  - [10.5 Vendor Firmware 与产品物料](#ch10-5)
- [11. 阶段五：Firmware 汇聚、签名与 PAC 输出](#ch11)
  - [11.1 整机物料汇聚](#ch11-1)
  - [11.2 AP / Boot 签名](#ch11-2)
  - [11.3 CP 固件处理](#ch11-3)
  - [11.4 PAC 打包链](#ch11-4)
  - [11.5 Release 输出](#ch11-5)
  - [11.6 SWU 分支状态](#ch11-6)
- [12. BBA 3.3.0 SDK 接入机制](#ch12)
  - [12.1 BBA 层级定位](#ch12-1)
  - [12.2 Supplier Adapter](#ch12-2)
  - [12.3 M8280 Model Overlay](#ch12-3)
  - [12.4 `ql_build_config` 拆分](#ch12-4)
  - [12.5 `env_build`](#ch12-5)
  - [12.6 `boot_build`](#ch12-6)
  - [12.7 `kernel_build`](#ch12-7)
  - [12.8 `modules_build`](#ch12-8)
  - [12.9 `apps_build`](#ch12-9)
  - [12.10 `fs_build`](#ch12-10)
  - [12.11 BBA RootFS](#ch12-11)
  - [12.12 `image_build`](#ch12-12)
  - [12.13 SDK RootFS 与 BBA RootFS 关系](#ch12-13)
- [13. BBA 3.3.0 全量构建阶段映射](#ch13)
  - [13.1 顶层构建命令](#ch13-1)
  - [13.2 阶段映射表](#ch13-2)
  - [13.3 完整产物流](#ch13-3)
- [14. 增量构建、Stamp 与 Build Cache](#ch14)
  - [14.1 Package Stamp](#ch14-1)
  - [14.2 Staging 记录](#ch14-2)
  - [14.3 Kernel Build Cache](#ch14-3)
  - [14.4 Boot Build Cache](#ch14-4)
  - [14.5 Make Recipe Shell 环境](#ch14-5)
  - [14.6 修改对象与重编范围](#ch14-6)
- [15. 产物反查与源码索引](#ch15)
  - [15.1 产物 Producer 索引](#ch15-1)
  - [15.2 构建异常定位索引](#ch15-2)
  - [15.3 核心源码入口](#ch15-3)
  - [15.4 当前证据边界](#ch15-4)
- [附录 A. 核心数据源](#appendix-a)

---

<a id="ch0"></a>
# 0. 文档范围与工程基线

<a id="ch0-1"></a>
## 0.1 文档范围

本文描述 M8280 / RG258UB_GLAB / UIS8510 / v610 当前工程的 SDK Build System，以及 BBA 3.3.0 在该 SDK 之上的产品化接入。

正文主线覆盖：

```text
产品配置
    ↓
Build 环境
    ↓
Boot / Kernel / Module / Package
    ↓
SDK RootFS
    ↓
Recovery / Vendor Firmware / NV
    ↓
Signing / PAC
    ↓
BBA 分阶段接入与 BBA RootFS
```

本文将以下对象严格区分：

- SDK Gold baseline；
- 当前 BBA 3.3.0 工作树；
- OpenWrt Build Framework；
- Unisoc / Quectel Vendor Build；
- BBA Supplier Adapter；
- BBA Model Overlay；
- SDK Native RootFS；
- BBA 最终产品 RootFS。

历史 `/4build` 工作树只用于已经闭环的结构性结论，不作为当前源码路径。

<a id="ch0-2"></a>
## 0.2 当前工程基线

| 项目 | 当前值 |
|---|---|
| 正式工程根 | `/home/bba/work/bba/610/bba/3.3.0/bba_3_0_platform` |
| BBA Branch | `3.3.0` |
| MODEL / SPEC | `M8280 / EU` |
| Quectel Project | `RG258UB_GLAB` |
| Revision | `RG258UB_GLABR01A01M4G` |
| Custom | `STD` |
| SoC | `UIS8510` |
| Platform | `v610` |
| Board | `1H10 NAND` |
| Kernel | Linux 6.6 |
| Flash | 256 MiB SPI NAND |
| SDK | `sdk/ql_rg620ua` |
| Model | `platform/build/model/M8280/EU` |
| BBA Filesystem | `platform/targets/M8280/EU/filesystem` |
| BBA Image | `platform/targets/M8280/EU/image` |

Supplier 文件名中的 `quecopen_rg620ua` 属于共享适配入口和历史命名。当前目标硬件仍为 RG258UB-GL / UIS8510 / v610。

<a id="ch0-3"></a>
## 0.3 Gold SDK 与 BBA 当前工作树

当前 New SDK Gold commit：

```text
fc1b1da38c0b2ea9b327a3c8b7f744c2a96df4f0
```

该 baseline 已完成：

- clean build；
- PAC 生成；
- 实机烧录；
- Bootloader 启动；
- Linux 6.6 启动；
- NAND / MTD / UBI；
- system SquashFS；
- Recovery RootFS。

BBA 3.3.0 已完成基于该 Gold SDK 的核心 rebase，并完成 Boot、Kernel、BBA RootFS、SecureBoot / PAC 与实机启动闭环。

Gold baseline 用于定义 SDK 原生实现；BBA 当前源码用于定义 M8280 产品实际实现。两者发生差异时，在正文中分别标记为“SDK 原生”和“BBA Adapter”。

<a id="ch0-4"></a>
## 0.4 证据边界

主流程使用当前源码、当前构建结果和已经闭环的 Gold / BBA 实机记录。以下内容不作为本文主流程结论：

- PAC 私有二进制容器内部格式；
- QFlash / FDL2 烧录命令执行细节；
- SWUpdate / qlfota Runtime 状态机；
- 闭源 CP firmware 内部 Build；
- 未经当前源码或构建结果证明的平台通用行为。

构建规则存在能力分支而当前配置未启用时，仅描述实现能力，不写为当前产品实际执行路径。

<a id="ch0-5"></a>
## 0.5 与刷机指南的内容边界

《M8280 / RG258UB_GLAB / UIS8510 / v610 完整刷机指南》已详细覆盖：

- PAC Item；
- Partitions.ini；
- pac.ini；
- Partitions.xml；
- raw MTD / UBI Volume 映射；
- QFlash；
- FDL / FDL2；
- Repartition；
- Erase；
- Write；
- Reset。

本文在 PAC 生成处完成 Build System 闭环，不重复展开 PAC 内部所有下载项和后续烧录时序。

---

<a id="ch1"></a>
# 1. SDK Build System 全局架构

本章给出整个 Build 的阶段模型。后续各章分别展开一个阶段，不跨章节穿插其他 subsystem 的实现。

<a id="ch1-1"></a>
## 1.1 Build 输入与输出

当前 SDK Build 的主要输入包括：

| 输入类型 | 当前对象 |
|---|---|
| 产品身份 | `RG258UB_GLAB / RG258UB_GLABR01A01M4G / STD` |
| OpenWrt 产品配置 | `config/defconfig_unisoc610_nand` |
| Kernel 配置 | `target/linux/unisoc/v610/config-default-nand` |
| Device | `DEVICE_uis8510_1h10_nand` |
| DTS | `unisoc/linux/kernel_6.6/arch/arm64/boot/dts/sprd/uis8510-1h10-nand.dts` |
| Boot Source | `unisoc/chipram4`、`unisoc/uboot44` |
| Linux Source | `unisoc/linux/kernel_6.6` |
| OpenWrt Package | `package/`、`feeds/` |
| Quectel Service | `quectel/services/`、`quectel/hal/` |
| Vendor Prebuilt | SML / TOS / TEECFG / SP / ADSP 等 |
| Product Data | boardcfg / NV / logo / Project 信息 |
| PAC Metadata | PAC INI / Partition XML |

主要输出包括：

```text
FDL1 / SPL / FDL2 / U-Boot
Image / Image.gz / DTB / boot.img
Kernel .ko / kmod
Userspace IPK
SDK TARGET_DIR
SDK root.squashfs
recovery.squashfs
NV / logo / Vendor firmware
signed images
PAC
```

<a id="ch1-2"></a>
## 1.2 五阶段 Build 模型

当前 SDK 完整构建可以划分为五个连续阶段：

```text
阶段 1
产品配置与构建环境
    │
    │  .config
    │  Project / Board 环境
    │  Host tools / Cross toolchain
    ▼
阶段 2
组件构建
    ├─ Boot
    ├─ Kernel / DTB / boot.img
    ├─ Kernel Module
    └─ Userspace Package
    │
    │  FDL / SPL / U-Boot
    │  Image / DTB / boot.img
    │  .ko / kmod / IPK
    ▼
阶段 3
SDK RootFS 组装
    │
    │  selected IPK
    │  opkg --offline-root
    │  TARGET_DIR
    │  root.squashfs
    ▼
阶段 4
Recovery 与整机附属物料
    │
    │  recovery.squashfs
    │  NV / logo
    │  Vendor firmware
    ▼
阶段 5
Firmware 汇聚、签名与 PAC
    │
    │  bin/unisoc/temp
    │  signed image
    │  cp_sign
    ▼
*.pac
```

阶段 1 只建立当前产品的 Build 上下文。阶段 2 负责把各独立 subsystem 构造成可打包对象。阶段 3 把 Package 转换为文件系统。阶段 4 补齐 Recovery 和整机其他 firmware。阶段 5 处理 Firmware Assembly、Signing 和 PAC Packaging。

<a id="ch1-3"></a>
## 1.3 Gold SDK 原生顶层入口

Gold baseline 的原生入口为：

```bash
source quectel/unisoc/compile/ql_build_config
buildconfig RG258UB_GLAB RG258UB_GLABR01A01M4G STD
build_fw
```

Gold `build_fw()` 是单体整机 Build 函数，主流程为：

```text
buildconfig
    ↓
产品环境建立
    ↓
build_fw
    ├─ 清理 bin/target 与 bin/unisoc/temp
    ├─ 同步 defconfig → .config
    ├─ make -j8 V=s
    ├─ build_nvitem
    ├─ check_rootfs_data
    ├─ build_deltanv
    ├─ build_logo
    ├─ 汇聚 AP / Boot / Linux / Recovery 物料
    ├─ build_sign
    ├─ build_pac
    ├─ 生成 release 目录
    └─ fota 参数存在时进入 SWU 生成入口
```

Gold `ql_build_config` 中不存在 `build_openwrt()` 和 `build_fw_pack()`。这两个函数属于 BBA 对 Gold `build_fw()` 的后续拆分。

<a id="ch1-4"></a>
## 1.4 阶段接口与主要产物

| 阶段 | 核心输入 | 核心输出 | 后续消费者 |
|---|---|---|---|
| 产品配置与环境 | Project / Revision / Custom / defconfig | `.config`、Build 环境 | 所有组件 Build |
| Boot | Boot source / Boot config | FDL / SPL / U-Boot | Firmware Pack |
| Kernel | Kernel config / DTS | Image / DTB / boot.img / `.ko` | kmod / PAC |
| Package | `CONFIG_PACKAGE_*` / Package Makefile | `.pkgdir` / IPK / staging | RootFS |
| SDK RootFS | selected IPK | TARGET_DIR / root.squashfs | Firmware Pack |
| Recovery | Recovery Package Set | recovery.squashfs | Firmware Pack |
| Firmware Pack | 全部 image / metadata | signed image / PAC | QFlash / Release |

<a id="ch1-5"></a>
## 1.5 BBA 分阶段接入概览

BBA 3.3.0 不直接执行 Gold 单体 `build_fw()`。BBA 将构建过程拆为：

```text
env_build
boot_build
kernel_build
modules_build
apps_build
fs_build
image_build
```

其中 SDK 组件仍由 OpenWrt / Unisoc / Quectel 原生 Framework 构建；BBA 在中间加入自己的：

- Model Overlay；
- public/private apps；
- public/private modules；
- filesystem；
- RootFS 组装；
- Product packaging delta。

最终 BBA RootFS 再回到 Quectel Firmware Packaging：

```text
SDK package
    ↓
SDK staging runtime
    ↓
BBA filesystem
    ↓
BBA root.squashfs
    ↓
build_fw_pack(external_rootfs)
    ↓
sign / PAC
```

---

<a id="ch2"></a>
# 2. Build System 核心对象与目录

本章只定义后续反复出现的配置对象、Framework 和目录。具体构建动作在后续阶段章节展开。

<a id="ch2-1"></a>
## 2.1 产品配置对象

### 2.1.1 OpenWrt 产品 defconfig

当前文件：

```text
sdk/ql_rg620ua/config/defconfig_unisoc610_nand
```

它是 SDK/OpenWrt 顶层产品配置，包含：

```text
CONFIG_TARGET_*
CONFIG_PACKAGE_*
CONFIG_KERNEL_*
CONFIG_ROOTFS_*
...
```

该文件不是 Linux Kernel `.config`。

### 2.1.2 SDK `.config`

当前文件：

```text
sdk/ql_rg620ua/.config
```

它是 OpenWrt Build Framework 当前实际读取的工作配置。`buildconfig()` 会比较 defconfig 与 `.config`，不一致时重新执行对应 defconfig target。

### 2.1.3 Linux Kernel `.config`

Linux 最终配置位于实际 Kernel 源码树：

```text
sdk/ql_rg620ua/unisoc/linux/kernel_6.6/.config
```

它由 OpenWrt Kernel 配置合并流程生成，不与 SDK `.config` 等价。

### 2.1.4 Boot 配置

Chipram 和 U-Boot 分别使用自身配置体系。对于 U-Boot，源码 defconfig、Target build_dir `.config` 和 generated config 是不同层级：

```text
source defconfig
    ↓
target build_dir/.config
    ↓
include/generated/autoconf.h
include/config/auto.conf
    ↓
binary
```

<a id="ch2-2"></a>
## 2.2 OpenWrt Target 层级

当前产品对应层级：

```text
OpenWrt generic
    ↓
target = unisoc
    ↓
subtarget = v610
    ↓
device = uis8510_1h10_nand
```

当前顶层配置包含：

```text
CONFIG_TARGET_unisoc=y
CONFIG_TARGET_unisoc_v610=y
CONFIG_TARGET_unisoc_v610_DEVICE_uis8510_1h10_nand=y
```

`RG258UB_GLAB` 是 Quectel Product；`M8280 / EU` 是 BBA Product。它们位于 OpenWrt Device 层之上。

<a id="ch2-3"></a>
## 2.3 Build Framework 主文件

| 文件 | 核心职责 |
|---|---|
| `sdk/ql_rg620ua/Makefile` | OpenWrt 顶层入口 |
| `sdk/ql_rg620ua/rules.mk` | BUILD_DIR / STAGING_DIR / TARGET_DIR 等公共变量 |
| `sdk/ql_rg620ua/include/package.mk` | Package Framework |
| `sdk/ql_rg620ua/include/package-pack.mk` | IPK / `.pkgdir` / STAGING_DIR_ROOT 等规则 |
| `sdk/ql_rg620ua/include/rootfs.mk` | Package install 后的 RootFS 整理 |
| `sdk/ql_rg620ua/include/kernel.mk` | Kernel / KernelPackage 公共定义 |
| `sdk/ql_rg620ua/include/kernel-build.mk` | Kernel compile/install 主 target |
| `sdk/ql_rg620ua/include/kernel-defaults.mk` | Kernel config / compile default 实现 |
| `sdk/ql_rg620ua/include/image.mk` | RootFS / DTS / image framework |
| `sdk/ql_rg620ua/target/linux/unisoc/` | Unisoc target / subtarget / image 定义 |

<a id="ch2-4"></a>
## 2.4 构建目录与输出目录

`rules.mk` 定义的当前主要目录为：

| 变量 / 目录 | 当前路径 | 作用 |
|---|---|---|
| `BUILD_DIR` | `build_dir/target-aarch64_cortex-a55_musl` | Target 组件构建工作区 |
| `STAGING_DIR` | `staging_dir/target-aarch64_cortex-a55_musl` | Target Sysroot、metadata、runtime staging |
| `TARGET_DIR` | `build_dir/target-aarch64_cortex-a55_musl/root-unisoc` | SDK 最终目标 RootFS 工作树 |
| `STAGING_DIR_ROOT` | `staging_dir/target-aarch64_cortex-a55_musl/root-unisoc` | Package runtime staging 合并树 |
| `PKG_INFO_DIR` | `staging_dir/target-aarch64_cortex-a55_musl/pkginfo` | Package install metadata |
| `PACKAGE_DIR` | `bin/packages` | IPK 仓库 |
| `KERNEL_BUILD_DIR` | `build_dir/.../linux-unisoc_v610` | v610 Kernel / image 工作目录 |
| `bin/unisoc/temp` | `bin/unisoc/temp` | Firmware assembly / signing / PAC 工作区 |
| `bin/target/<REV>` | `bin/target/RG258UB_GLABR01A01M4G` | SDK Release 输出 |

其中：

```text
STAGING_DIR_ROOT != TARGET_DIR
```

这是当前 v610 SDK 与 BBA RootFS 接入最关键的目录边界之一。

---

<a id="ch3"></a>
# 3. 阶段一：产品配置与构建环境

本阶段从 Project / Revision / Custom 开始，输出 OpenWrt `.config`、平台映射、Feed 状态和编译工具环境。Boot、Kernel 和 Package 尚未在本阶段展开。

<a id="ch3-1"></a>
## 3.1 `ql_build_config` 初始化

Gold SDK：

```text
sdk/ql_rg620ua/quectel/unisoc/compile/ql_build_config
```

被 `source` 时建立：

```sh
export TOPDIR=$(pwd)
export UNISOCDIR=${TOPDIR}/unisoc
export QUECTELDIR=${TOPDIR}/quectel
mkdir -p ${TOPDIR}/bin/unisoc/temp/
source ${QUECTELDIR}/unisoc/compile/ql_build_product
```

因此：

```text
ql_build_config
    ├─ 建立 SDK 顶层路径
    ├─ 建立 Unisoc / Quectel 路径
    ├─ 准备 Firmware temp 目录
    └─ 引入 ql_build_product
```

<a id="ch3-2"></a>
## 3.2 `buildconfig()` 主流程

入口：

```text
quectel/unisoc/compile/ql_build_config
buildconfig()
```

Gold 主流程：

```text
buildconfig()
    ↓
unisoc_env_check
    ↓
buildconfig_product(Project, Revision, Custom)
    ↓
unset_unisoc_env
    ↓
Product → Platform / Machine / Defconfig 映射
    ↓
scripts/feeds update -a
scripts/feeds install -a
    ↓
defconfig 与 .config 比较
    ↓
必要时 make defconfig_unisoc610_nand
    ↓
复制产品 bsp.config
```

`buildconfig()` 同时承担产品身份和 OpenWrt Build 环境两类职责。

<a id="ch3-3"></a>
## 3.3 Project / Revision / Custom 处理

产品配置逻辑位于：

```text
sdk/ql_rg620ua/quectel/unisoc/compile/ql_build_product
```

当前输入：

```text
Project  = RG258UB_GLAB
Revision = RG258UB_GLABR01A01M4G
Custom   = STD
```

该层完成：

- Project 合法性检查；
- Customer / Custom 合法性检查；
- `quectel-buildconfig-gen.h` 生成；
- `base-files/etc/config/projectinfo` 生成。

这些对象后续进入编译宏、RootFS 和固件产品信息。

<a id="ch3-4"></a>
## 3.4 RG258UB_GLAB 平台映射

Gold `ql_build_config` 对 RG258UB 系列的当前映射为：

```text
RG258UB_GLAB
    │
    ├─ NWMODE         = UIS8510_1H10_SEC
    ├─ UNISOC_PRODUCT = cpe
    ├─ modem_name     = 5g_modem_v2_24a_v610
    ├─ platform_name  = uis8510
    │
    ├─ MACHINENAME    = uis8510-1h10-nand
    ├─ MACHINE        = uis8510-1h10-nand
    ├─ board_name     = uis8510_1h10_nand
    └─ defconfig      = defconfig_unisoc610_nand
```

因此产品身份在该阶段已经收敛为：

```text
RG258UB_GLAB
    ↓
UIS8510
    ↓
v610
    ↓
1H10 NAND
    ↓
defconfig_unisoc610_nand
```

OpenWrt Device 的具体选择继续由 `defconfig_unisoc610_nand` 中的 `CONFIG_TARGET_*` 完成。

<a id="ch3-5"></a>
## 3.5 OpenWrt 顶层配置生成

`buildconfig()` 比较：

```text
config/defconfig_unisoc610_nand
```

与：

```text
.config
```

内容存在差异时执行：

```bash
make defconfig_unisoc610_nand
```

最终 SDK `.config` 用于后续：

```text
Target / Subtarget / Device 选择
Package 选择
CONFIG_KERNEL_* 转换
RootFS / SecureBoot 选项
Image 规则条件
```

配置链可以表示为：

```text
Project
    ↓
defconfig = defconfig_unisoc610_nand
    ↓
config/defconfig_unisoc610_nand
    ↓
make defconfig_unisoc610_nand
    ↓
SDK .config
```

<a id="ch3-6"></a>
## 3.6 Feed 初始化

Gold `buildconfig()` 执行：

```bash
scripts/feeds update -a
scripts/feeds install -a
```

Feed 处理后，Quectel Services 等 Package 能通过：

```text
package/feeds/<feed>/<package>
```

进入 OpenWrt Package Framework。后续 Package 选择、`.packageinfo` 与 `.packagedeps` 均基于该 Package Tree。

<a id="ch3-7"></a>
## 3.7 Host Tools 与 Cross Toolchain

当前 v610 New SDK 使用预置工具：

```text
sdk/ql_rg620ua/host/linux64
sdk/ql_rg620ua/owtoolchain/linux64
```

对应 staging 入口：

```text
staging_dir/host
staging_dir/toolchain-aarch64_cortex-a55_gcc-13.3.0_musl
```

当前 target toolchain 关键变量：

```text
HOST          = aarch64-openwrt-linux-musl
TOOLPREFIX    = aarch64-openwrt-linux-musl-
CC            = aarch64-openwrt-linux-musl-gcc
CXX           = aarch64-openwrt-linux-musl-g++
CROSS_COMPILE = aarch64-openwrt-linux-musl-
STAGING_DIR   = staging_dir/target-aarch64_cortex-a55_musl
```

M8280 当前 BBA `supplier_env_build` 只检查预置 host/toolchain 和 staging 链接，不再执行旧 SDK 的：

```text
make tools/compile
make toolchain/compile
```

该差异属于 New SDK 适配后的当前有效实现。

<a id="ch3-8"></a>
## 3.8 阶段输出

阶段一完成后，系统已经具备：

```text
确定的 Product / Machine / Device
OpenWrt .config
Feed Package Tree
Host Build Tools
AArch64 Cross Toolchain
Target Sysroot 基础路径
```

此时尚不能将 `.config` 中某个 Package 或 Kernel 选项直接等价为最终固件文件。后续组件 Build 和 RootFS Install 仍需分别完成。

---

<a id="ch4"></a>
# 4. 阶段二-A：Boot 构建

本阶段只处理 Chipram4 / SPL / FDL / U-Boot。Linux Kernel 和 RootFS 不属于本章。

<a id="ch4-1"></a>
## 4.1 Boot Package 入口

当前 M8280 的 Boot Package target：

```bash
make package/boot/chipram4-unisoc/compile
make package/boot/uboot44-unisoc/compile
```

BBA 当前 `supplier_boot_build` 会在同一个 recipe shell 中重新：

```bash
source quectel/unisoc/compile/ql_build_config
buildconfig RG258UB_GLAB RG258UB_GLABR01A01M4G STD
```

随后执行上述两个 target。

这保证 `SECBOOT_ENABLE`、`USERDEBUG`、`UNISOC_PRODUCT` 等由 `buildconfig` 建立的变量在 Boot Package 运行时存在。

<a id="ch4-2"></a>
## 4.2 Chipram4 / SPL 构建

当前平台使用：

```text
sdk/ql_rg620ua/unisoc/chipram4
```

Boot Package 通过 OpenWrt Package target 将 Unisoc Chipram 构建纳入 SDK Build。

该阶段产生 Early Boot / Download 相关物料，其中包括：

```text
fdl1.bin
u-boot-spl-16k.bin
```

最终 Firmware Packaging 再根据 SecureBoot 配置生成对应 signed image。

<a id="ch4-3"></a>
## 4.3 U-Boot44 构建

当前 U-Boot 源码：

```text
sdk/ql_rg620ua/unisoc/uboot44
```

M8280 / 1H10 NAND 对应 config：

```text
unisoc/uboot44/configs/uis8510_1h10_nand_defconfig
```

`uboot44-unisoc` Package 输出当前后续 Firmware Pack 使用的：

```text
fdl2.bin
u-boot.bin
```

当前曾出现某一版 `fdl2.bin` 与 `u-boot.bin` 内容相同；本文不据此定义二者内部架构关系，只保留它们作为不同 Firmware Item 的 Build 输出身份。

<a id="ch4-4"></a>
## 4.4 Boot 构建配置层级

U-Boot 配置至少存在三层：

```text
源码配置
unisoc/uboot44/configs/uis8510_1h10_nand_defconfig
        ↓
Target Build 配置
build_dir/target-aarch64_cortex-a55_musl/u-boot44-*/.config
        ↓
Generated Config
include/generated/autoconf.h
include/config/auto.conf
u-boot.cfg
        ↓
U-Boot Binary
```

最终 Binary 由 Target build_dir 中实际展开后的配置决定。

Host 侧存在的：

```text
build_dir/host/u-boot-*/
```

不代表 UIS8510 目标板 U-Boot Build。

<a id="ch4-5"></a>
## 4.5 Boot 主要产物

Boot 阶段对后续打包的主要输出可以归纳为：

| 产物 | 来源 |
|---|---|
| `fdl1.bin` | Chipram4 / FDL1 |
| `u-boot-spl-16k.bin` | Chipram4 / SPL |
| `fdl2.bin` | U-Boot44 Download 环境 |
| `u-boot.bin` | U-Boot44 |
| Boot symbol | `bin/symbol/chipram/...`、对应 U-Boot symbol |

这些文件随后由 `build_fw()` 或 BBA `build_fw_pack()` 汇入 `bin/unisoc/temp`。

<a id="ch4-6"></a>
## 4.6 Boot Build Cache

M8280 已经出现过以下实际情况：

```text
source defconfig = 115200
Target build_dir/.config = 921600
generated config = 921600
```

最终 Binary 仍使用旧 Target 配置。

因此 Boot 配置修改的判定链为：

```text
source defconfig
    ↓
Target .config
    ↓
generated config
    ↓
binary
```

源码文件出现新值只证明输入已经修改，不能单独证明目标 Binary 已刷新。

---

<a id="ch5"></a>
# 5. 阶段二-B：Linux Kernel、DTS / DTB 与 boot.img

本阶段覆盖 Linux 6.6 配置、Kernel Image、Device Tree 和 boot.img。Kernel Module 的 Package 化在第 6 章单独展开。

<a id="ch5-1"></a>
## 5.1 Kernel Build 入口

BBA 当前 Kernel target：

```bash
make target/linux/{compile,install}
```

随后当前 BBA 还显式执行：

```bash
make -C target/linux/unisoc/image boot-img \
    TOPDIR="<SDK>" \
    TARGET_BUILD= \
    BOARD=unisoc \
    SUBTARGET=v610
```

SDK Kernel Framework 主入口：

```text
include/kernel.mk
include/kernel-build.mk
include/kernel-defaults.mk
target/linux/unisoc/
```

<a id="ch5-2"></a>
## 5.2 External Kernel Tree

SDK OpenWrt Framework 仍保留：

```text
KERNEL_PATCHVER := 5.4
CONFIG_LINUX_5_4=y
```

当前实际 Kernel Source 由：

```text
CONFIG_EXTERNAL_KERNEL_TREE="$(TOPDIR)/unisoc/linux/kernel_6.6"
```

指定。

OpenWrt Kernel 工作目录中曾确认：

```text
build_dir/target-aarch64_cortex-a55_musl/
linux-unisoc_v610/
    linux-5.4.xxx -> .../unisoc/linux/kernel_6.6
```

因此：

```text
OpenWrt Kernel Framework Version
        = 5.4 目录/框架标识

实际 Kernel Source
        = unisoc/linux/kernel_6.6
```

Linux 最终 `.config` 和实际源码编译均作用于 6.6 External Tree。

<a id="ch5-3"></a>
## 5.3 Kernel 配置选择

当前 Device：

```text
DEVICE_uis8510_1h10_nand
```

会使 Unisoc target 使用 NAND Kernel config：

```text
target/linux/unisoc/v610/config-default-nand
```

同层候选顺序为：

```text
config-default-$(KERNEL_CONFIG_FILE_NAME_APPENDIX)
config-$(KERNEL_PATCHVER)
config-default
```

当前 `KERNEL_CONFIG_FILE_NAME_APPENDIX=nand`，因此命中 `config-default-nand`。

该选择不是“先加载 config-default，再叠加 nand 差异”，而是在 v610 层选择一个实际 Kernel config 文件。

<a id="ch5-4"></a>
## 5.4 Kernel `.config` 合并

Kernel 配置链为：

```text
generic Kernel config
    +
unisoc target Kernel config
    +
v610/config-default-nand
    +
env/kernel-config（存在时）
    ↓
scripts/kconfig.pl "+"
    ↓
.config.target
    ↓
追加 SDK .config 中 CONFIG_KERNEL_* 转换项
    ↓
package-metadata.pl
    ↓
.config.override
    ↓
scripts/kconfig.pl "m+"
    ↓
.config.set
    ↓
最终 Linux .config
```

SDK `.config` 中：

```text
CONFIG_KERNEL_FOO=y
```

在 Kernel 配置生成阶段会转换为：

```text
CONFIG_FOO=y
```

后续 Package metadata 还可以向 Kernel Kconfig 注入依赖选项。

因此 Kernel 宏的最终判定对象是：

```text
unisoc/linux/kernel_6.6/.config
```

而不是单独看：

```text
config.sdk
config.kernel
config-default-nand
SDK .config
```

<a id="ch5-5"></a>
## 5.5 Kernel Image 编译

Kernel image 编译由：

```text
Kernel/CompileImage/Default
```

触发：

```make
$(KERNEL_MAKE) ... $(KERNELNAME)
```

当前 BBA `v610.mk`：

```text
KERNELNAME := Image.gz dtbs
```

因此当前产品实际 Kernel Build 会生成：

```text
Image.gz
DTB
```

并保留 Linux 侧的 `Image`。

当前已经确认的典型路径：

```text
unisoc/linux/kernel_6.6/arch/arm64/boot/Image
unisoc/linux/kernel_6.6/arch/arm64/boot/Image.gz
```

Gold 原生 `v610.mk` 为：

```text
KERNELNAME := Image dtbs
```

而其 `Build/make-boot-img` 读取 `Image.gz`。Gold 单体 Build 中该 `Image.gz` 的保证来源未在旧 Node 6 单独闭环；当前 BBA 已通过 `KERNELNAME := Image.gz dtbs` 明确消除这一边界。

<a id="ch5-6"></a>
## 5.6 Device 与 DTS 映射

v610 Device 定义：

```make
define Device/uis8510_1h10_nand
  DEVICE_VENDOR := QUECTEL V610 Module
  DEVICE_MODEL := RG258UB/QRM258UBP
  SUPPORTED_DEVICES += uis8510_1h10_nand
  DEVICE_DTS := sprd/uis8510-1h10-nand
endef
```

因此链路为：

```text
CONFIG_TARGET_unisoc_v610_DEVICE_uis8510_1h10_nand=y
    ↓
Device/uis8510_1h10_nand
    ↓
DEVICE_DTS=sprd/uis8510-1h10-nand
    ↓
uis8510-1h10-nand.dts
```

DTS 不是由 `MACHINENAME` 字符串自动推导，而由 OpenWrt Device 定义显式建立映射。

<a id="ch5-7"></a>
## 5.7 DTB 编译

`include/image.mk`：

```text
DTS_DIR := $(LINUX_DIR)/arch/$(LINUX_KARCH)/boot/dts
```

当前：

```text
LINUX_KARCH=arm64
```

因此目标 DTB：

```text
unisoc/linux/kernel_6.6/
arch/arm64/boot/dts/sprd/
uis8510-1h10-nand.dtb
```

Linux DTS Makefile 已登记：

```text
uis8510-1h10-nand.dtb
```

当前 `KERNELNAME` 包含 `dtbs`，实际执行 Linux Kernel 原生：

```text
make dtbs
```

当前 v610 `boot.img` 使用该 Kernel 原生 DTB，不读取 OpenWrt 另一套 `Image/BuildDTB` 生成的 `$(KDIR)/image-*.dtb`。

<a id="ch5-8"></a>
## 5.8 `boot.img` 组装

当前 v610 Boot Image 输入：

```text
Image.gz
    ↓
kernel.img

uis8510-1h10-nand.dtb
    ↓
dt.img

dummy ramdisk
```

随后：

```text
kernel.img
+
ramdisk.img
+
dt.img
    ↓
target/linux/unisoc/image/mkkernelimg.py
    ↓
boot.img
```

`mkkernelimg.py` 使用 `UNISOCBOOTIMAGE!` Header，并记录 kernel size、ramdisk size、load address、page size 和 DT size。

当前 ramdisk 是 placeholder：

```text
This is not an initrd
```

真正系统 RootFS 为独立 `root.squashfs`。

<a id="ch5-9"></a>
## 5.9 阶段输出

本阶段完成后可供后续打包使用的主要对象：

```text
Image / Image.gz
uis8510-1h10-nand.dtb
boot.img
Linux modules
vmlinux / symbol
```

`boot.img` 进入后续 Firmware Assembly；Linux modules 继续进入第 6 章的 KernelPackage / RootFS 安装链。

---

<a id="ch6"></a>
# 6. 阶段二-C：Kernel Module 构建

本章区分两个动作：

```text
Linux Kernel 编译 .ko
```

与：

```text
OpenWrt KernelPackage 将 .ko 组织成 kmod
```

两者不是同一个 Build 阶段。

<a id="ch6-1"></a>
## 6.1 Kernel Module 编译层

当前 M8280 `config.kernel` 中存在：

```text
CONFIG_NETFILTER_XT_SET=m
```

BBA `supplier_kernel_prepare` 将该配置写入 v610 Kernel config 输入。

`target/linux/compile` 进入：

```text
include/kernel-build.mk
```

其中：

```text
$(LINUX_DIR)/.modules
    ↓
Kernel/CompileModules
    ↓
Kernel/CompileModules/Default
    ↓
$(KERNEL_MAKE) ... modules
```

所以：

```text
CONFIG_xxx=m
    ↓
Linux Kbuild
    ↓
*.ko
```

发生在 `target/linux/compile`。

<a id="ch6-2"></a>
## 6.2 `KernelPackage` 打包层

BBA 后续执行：

```bash
make package/kernel/linux/compile
```

`package/kernel/linux/Makefile` 载入：

```text
modules/*.mk
target-specific module definitions
```

`include/kernel.mk` 的 `KernelPackage` 负责把已存在的 `.ko` 组织为：

```text
kmod-<name>
```

典型 install 行为：

```text
FILES
    ↓
检查 modules.builtin
    ↓
检查 .ko 是否存在
    ↓
copy
    ↓
lib/modules/$(LINUX_UNAME_VERSION)/
```

因此 `package/kernel/linux/compile` 的主要职责是 Kernel module package framework，不是 Linux `.ko` 的首次编译入口。

<a id="ch6-3"></a>
## 6.3 `kmod-ipt-ipset` 实例

当前输入：

```text
platform/build/model/M8280/EU/config.kernel
CONFIG_NETFILTER_XT_SET=m
```

OpenWrt 产品配置：

```text
config/defconfig_unisoc610_nand
CONFIG_PACKAGE_kmod-ipt-ipset=y
```

完整关系：

```text
CONFIG_NETFILTER_XT_SET=m
    ↓
Linux Kbuild
    ↓
net/netfilter/xt_set.ko
    ↓
package/kernel/linux/modules/netfilter.mk
KernelPackage/ipt-ipset
    ↓
FILES += $(LINUX_DIR)/net/netfilter/xt_set.ko
    ↓
kmod-ipt-ipset
    ↓
lib/modules/$(LINUX_UNAME_VERSION)/
```

该实例同时说明：

```text
CONFIG_xxx=m
```

控制 Linux module 形态；

```text
CONFIG_PACKAGE_kmod-xxx=y
```

控制 OpenWrt 是否选择对应 kmod Package。

<a id="ch6-4"></a>
## 6.4 `nat46` 外置模块实例

BBA `supplier_modules_build` 还显式执行：

```bash
make package/kernel/nat46/compile
```

`nat46` 不直接来自 Linux source tree，而由自己的 Package Makefile：

```text
package/kernel/nat46/Makefile
```

执行：

```text
$(KERNEL_MAKE)
M="$(PKG_BUILD_DIR)/nat46/modules"
modules
```

输出：

```text
$(PKG_BUILD_DIR)/nat46/modules/nat46.ko
```

当前：

```text
CONFIG_PACKAGE_kmod-nat46
```

在 M8280 defconfig 中未选择。因此“显式执行 `nat46/compile`”只证明该 Package target 被构建，不足以证明 `nat46.ko` 一定进入最终 SDK RootFS。

<a id="ch6-5"></a>
## 6.5 Module 安装阶段

当前 `supplier_modules_install` 是空 target。

KernelPackage 的最终 RootFS 安装仍依赖后续 Package / Target install：

```text
Kernel .ko
    ↓
KernelPackage
    ↓
kmod IPK / package metadata
    ↓
package/install
    ↓
TARGET_DIR
```

BBA 最终 RootFS 中的 module 还要经过 BBA `fs_modules`：

```text
public_modules_install
private_modules_install
supplier_modules_install
```

因此：

```text
module 已编译
!=
module 已进入最终设备 RootFS
```

---

<a id="ch7"></a>
# 7. 阶段二-D：OpenWrt Userspace Package 构建

本章以 qlnet 为实证对象说明通用 Package Framework。qlnet 是预编译 ELF Package，因此 `Build/Compile` 为空；Framework 的 Prepare / Install / IPK / RootFS 机制仍具有通用意义。

<a id="ch7-1"></a>
## 7.1 Package 选择

当前产品配置：

```text
config/defconfig_unisoc610_nand
CONFIG_PACKAGE_qlnet=y
```

SDK `.config` 同样存在：

```text
CONFIG_PACKAGE_qlnet=y
```

该配置只表示 qlnet 被当前产品选择，不表示配置生成时立即执行 qlnet 编译。

<a id="ch7-2"></a>
## 7.2 Package 元数据与依赖图

OpenWrt 自动生成：

```text
tmp/.packageinfo
tmp/.packagedeps
tmp/.packageauxvars
tmp/.packageusergroup
```

qlnet 在 `.packagedeps` 中形成：

```text
package-$(CONFIG_PACKAGE_qlnet)
    += feeds/quectel_services/qlnet
```

当前配置展开后：

```text
package-y += feeds/quectel_services/qlnet
```

`DEPENDS` 同样会被转换为真实 Make dependency。例如 qlnet 依赖：

```text
ubus
uci
libubox
libqlutils
libqlril
libxml2
libjson-c
```

对应 dependency graph 会要求这些 Package 的 compile target 先满足。

<a id="ch7-3"></a>
## 7.3 `BuildPackage()`

Package Makefile 末尾：

```make
$(eval $(call BuildPackage,$(PKG_NAME)))
```

`BuildPackage()` 位于：

```text
include/package.mk
```

其职责是：

- 应用 `Package/Default`；
- 应用 `Package/<name>`；
- 注册 Package；
- 选择 `ipkg` 等 Build Target；
- 生成 Prepare / Configure / Compile / Package 等 Make Rules。

`BuildPackage()` 是规则生成入口，不等价于一次 gcc 执行。

<a id="ch7-4"></a>
## 7.4 Prepare / Configure / Compile

`include/package.mk` 的依赖顺序：

```text
STAMP_PREPARED
    ↓
Build/Prepare
    ↓
STAMP_CONFIGURED
    ↓
Build/Configure
    ↓
STAMP_BUILT
    ↓
Build/Compile
Build/Install
```

请求：

```bash
make package/.../compile
```

时，Make dependency 会自动补齐尚未完成的前置阶段。

当前 qlnet：

```make
define Build/Prepare
    mkdir -p $(PKG_BUILD_DIR)
    $(CP) $(SVC_SOURCE_DIR)/* $(PKG_BUILD_DIR)
endef

define Build/Compile
endef
```

原因是：

```text
quectel/services/qlnet/src/qlnet
```

已经是 AArch64 + musl ELF。

因此 qlnet 实际为：

```text
prebuilt ELF
    ↓
Build/Prepare：copy
    ↓
Build/Configure
    ↓
Build/Compile：空
    ↓
Package Assembly
```

`.built` 存在只表示 Framework Build 阶段完成，不代表一定调用过 C/C++ compiler。

<a id="ch7-5"></a>
## 7.5 `Build/InstallDev`

`Build/InstallDev` 面向后续 Package 编译所需的开发文件：

```text
header
shared library
static library
pkgconfig
```

标准路径：

```text
Package Build
    ↓
Build/InstallDev
    ↓
tmp/stage-<package>/
    ↓
记录贡献文件
    ↓
staging_dir/.../packages/<package>.list
    ↓
merge
    ↓
STAGING_DIR/usr/include
STAGING_DIR/usr/lib
```

这样 Package B 可以在自己的 compile/link 阶段直接使用 Package A 导出的 header 和 library。

`staging_dir/.../packages/<package>.list` 同时为后续 clean 提供文件追踪。

<a id="ch7-6"></a>
## 7.6 `Package/install` 与 `.pkgdir`

Runtime payload 由：

```make
define Package/<name>/install
    ...
endef
```

安装到 Package 自己的文件树。

以 qlnet 为例，Runtime 内容包括：

```text
/usr/bin/qlnet
/etc/init.d/qlnet.init
/etc/config/qlnet
/etc/config/qlapn
/etc/config/qlimsiapn
/etc/apns-conf_8.xml
/etc/numeric_operator.xml
```

Framework 形成：

```text
$(PKG_BUILD_DIR)/.pkgdir/qlnet/
```

`.pkgdir` 是该 Package Runtime Payload 的中间文件树。

<a id="ch7-7"></a>
## 7.7 `STAGING_DIR_ROOT`

`include/package-pack.mk` 已确认存在：

```text
$(STAGING_DIR_ROOT)/stamp/.<package>_installed
    ↓
copy $(PKG_BUILD_DIR)/.pkgdir/<package>/. 
    ↓
STAGING_DIR_ROOT
```

当前：

```text
STAGING_DIR_ROOT
=
staging_dir/target-aarch64_cortex-a55_musl/root-unisoc
```

它是多个 Package `.pkgdir` Runtime Payload 的 staging 合并树。

它不是：

```text
STAGING_DIR/usr/include + usr/lib
```

这种开发 Sysroot；

也不是：

```text
TARGET_DIR
```

这种经 IPK + opkg 形成的 SDK RootFS。

<a id="ch7-8"></a>
## 7.8 IPK 生成

默认 Package target 为：

```text
ipkg
```

精确定义位于：

```text
include/package-pack.mk
BuildTarget/ipkg
```

该流程生成：

```text
.pkgdir
    ├─ 原样 merge → STAGING_DIR_ROOT
    │
    └─ copy → IPKG IDIR
               ↓
             RSTRIP
               ↓
          CONTROL metadata
               ↓
            ipkg-build
               ↓
             *.ipk
```

IPK 输出到：

```text
bin/packages/
```

对应 Package install metadata 位于：

```text
staging_dir/.../pkginfo/
```

<a id="ch7-9"></a>
## 7.9 qlnet 构建实例

当前闭环链：

```text
CONFIG_PACKAGE_qlnet=y
    ↓
tmp/.packagedeps
    ↓
feeds/quectel_services/qlnet/Makefile
    ↓
quectel/services/qlnet/src/qlnet
    ↓
Build/Prepare
    ↓
build_dir/.../quectel-services/qlnet/
    ↓
Build/Compile = empty
    ↓
Package/qlnet/install
    ↓
.pkgdir/qlnet/
    ├────────────────→ STAGING_DIR_ROOT
    │
    └→ ipkg-aarch64_cortex-a55/qlnet/
          ↓
        RSTRIP
          ↓
bin/packages/quectel_services/
qlnet_1_aarch64_cortex-a55.ipk
```

实际文件曾确认：

```text
.pkgdir qlnet            ≈ 80K / unstripped
STAGING_DIR_ROOT qlnet   ≈ 80K / unstripped

IPK payload qlnet        ≈ 65K
TARGET_DIR qlnet         ≈ 65K
```

这组实证直接证明 STAGING_DIR_ROOT 与 TARGET_DIR 的文件来源和后处理路径不同。

---

<a id="ch8"></a>
# 8. 阶段三：SDK RootFS 组装

本阶段从已经生成的 Package / IPK 开始，输出 SDK Native RootFS 和 `root.squashfs`。

<a id="ch8-1"></a>
## 8.1 Package 安装清单

Package Framework 在：

```text
staging_dir/.../pkginfo/<package>.default.install
```

记录被选中 Package 的安装标识。

最终根据产品配置形成：

```text
tmp/opkg_install_list
```

其中包含当前固件需要安装的 IPK 路径。

qlnet 的关系为：

```text
qlnet.default.install
    ↓
PACKAGE_INSTALL_FILES
    ↓
tmp/opkg_install_list
    ↓
qlnet_*.ipk
```

<a id="ch8-2"></a>
## 8.2 `make package/install`

SDK RootFS 的核心安装入口：

```bash
make package/install
```

其职责为：

```text
准备 / 重建 TARGET_DIR
    ↓
读取 opkg_install_list
    ↓
host opkg --offline-root
    ↓
安装全部 selected IPK
    ↓
形成 TARGET_DIR
    ↓
prepare_rootfs
```

它不是“安装当前刚刚编译的某一个 Package”，而是按当前产品配置组装完整的 SDK Target RootFS。

<a id="ch8-3"></a>
## 8.3 `TARGET_DIR`

当前：

```text
TARGET_DIR
=
build_dir/target-aarch64_cortex-a55_musl/root-unisoc
```

该目录中的 Runtime 文件来自：

```text
IPK
    ↓
host opkg --offline-root
    ↓
TARGET_DIR
```

qlnet 已通过 MD5 确认：

```text
IPK payload qlnet
==
TARGET_DIR/usr/bin/qlnet
```

<a id="ch8-4"></a>
## 8.4 `prepare_rootfs`

定义：

```text
include/rootfs.mk
```

当前已确认的职责包括：

- 合并 `TOPDIR/files` overlay；
- 建立 `/etc/rc.d`；
- 建立 `/var/lock`；
- 执行 Package postinst；
- 处理 opkg status；
- 处理 init.d enable / disable；
- 清理 postinst 和临时 Package 信息；
- 执行后续 RootFS 整理。

因此：

```text
opkg install 完成
```

仍不是 SDK RootFS 的最终状态。

<a id="ch8-5"></a>
## 8.5 SDK `root.squashfs`

SDK Native image framework：

```text
include/image.mk
```

存在：

```text
$(KDIR)/root.%:
    $(call Image/mkfs/...)
```

SquashFS 路径：

```text
TARGET_DIR
    ↓
mksquashfs4
    ↓
KDIR/root.squashfs
```

当前逻辑目录：

```text
build_dir/target-aarch64_cortex-a55_musl/
linux-unisoc_v610/root.squashfs
```

Gold `build_fw()` 随后执行：

```text
find build_dir -name root.squashfs
    ↓
copy
    ↓
bin/unisoc/temp/root.squashfs
```

SecureBoot 开启时再生成：

```text
root-sign.squashfs
```

<a id="ch8-6"></a>
## 8.6 SDK Native RootFS 输出

SDK 原生 RootFS 链完整表示为：

```text
CONFIG_PACKAGE_*
    ↓
Package Build
    ↓
IPK
    ↓
tmp/opkg_install_list
    ↓
make package/install
    ↓
TARGET_DIR
    ↓
prepare_rootfs
    ↓
include/image.mk
    ↓
root.squashfs
```

这是 SDK Demo / SDK Native Firmware 的 RootFS 主链。

当前 BBA 产品不会直接把这份 SDK Native `root.squashfs` 作为最终 M8280 system RootFS，具体接入在第 12 章展开。

---

<a id="ch9"></a>
# 9. 构建目录与产物流转

前面各章已经定义 Build 时序。本章从目录视角统一整理各中间现场，避免把 `build_dir`、`staging_dir`、`TARGET_DIR` 和 Firmware `bin` 混为同一类输出。

<a id="ch9-1"></a>
## 9.1 `build_dir`

当前：

```text
build_dir/target-aarch64_cortex-a55_musl/
```

它是 Target Build 工作区，可同时包含：

```text
Package build workspace
Kernel build workspace
TARGET_DIR RootFS workspace
```

典型内容：

```text
quectel-services/qlnet/
linux-unisoc_v610/
root-unisoc/
busybox-*/
openssl-*/
...
```

因此 `build_dir` 不是最终 Release 目录。

<a id="ch9-2"></a>
## 9.2 `staging_dir` 开发 Sysroot

当前开发 Sysroot：

```text
staging_dir/target-aarch64_cortex-a55_musl/usr/include
staging_dir/target-aarch64_cortex-a55_musl/usr/lib
```

其核心用途是 Package 间编译依赖：

```text
Package A
    ↓
Build/InstallDev
    ↓
STAGING_DIR/usr/include + usr/lib
    ↓
Package B compile / link
```

其中可见 `ql_wan.h`、`libqlril.so`、`libubus.so`、`libssl.so` 等 Target Header / Library。

<a id="ch9-3"></a>
## 9.3 `STAGING_DIR_ROOT`

当前：

```text
staging_dir/target-aarch64_cortex-a55_musl/root-unisoc
```

它来自：

```text
各 Package .pkgdir
    ↓ direct copy
STAGING_DIR_ROOT
```

主要用途是 Runtime Payload Staging，不等价于 SDK Native RootFS。

当前 BBA Supplier Adapter 正是从这里选择性导入 Quectel Runtime。

<a id="ch9-4"></a>
## 9.4 `TARGET_DIR`

当前：

```text
build_dir/target-aarch64_cortex-a55_musl/root-unisoc
```

形成方式：

```text
selected IPK
    ↓
opkg --offline-root
    ↓
TARGET_DIR
```

因此其 Runtime Binary 可能已经经过 IPK 路径的 RSTRIP，与 STAGING_DIR_ROOT 中的文件不保证字节级一致。

<a id="ch9-5"></a>
## 9.5 `bin/packages`

当前：

```text
bin/packages
```

是独立 IPK 软件包仓库。

Package Framework 在这里输出：

```text
<package>_<version>_<arch>.ipk
```

Recovery RootFS 同样通过 offline opkg 使用 `bin/packages` 中的软件包。

<a id="ch9-6"></a>
## 9.6 `bin/unisoc/temp`

该目录不是普通 OpenWrt Package 输出，而是 Unisoc / Quectel 整机 Firmware 工作区。

典型内容：

```text
fdl1.bin
fdl2.bin
u-boot-spl-16k.bin
u-boot.bin
boot.img
root.squashfs
recovery.squashfs

sml.bin
teecfg.bin
tos.bin
UIS8510_SP.bin
ums9632_v610_adsp.bin

nvitem.bin
deltanv.bin
Project.bin
logo
Partition XML

*-sign.*
cp_sign/
```

签名、CP 处理和 PAC Packaging 都以该目录为核心工作现场。

<a id="ch9-7"></a>
## 9.7 Release 输出

SDK Release：

```text
bin/target/<QUECTEL_PROJECT_REV>/
bin/target/<QUECTEL_PROJECT_REV>_factory/
bin/target/<QUECTEL_PROJECT_REV>_symbols/
```

PAC 的真正生成现场位于：

```text
bin/unisoc/temp/cp_sign/<NWMODE>/
```

随后再复制到 standard / factory release。

<a id="ch9-8"></a>
## 9.8 Userspace ELF 文件流

以 qlnet 为例：

```text
quectel/services/qlnet/src/qlnet
    ↓
build_dir/.../quectel-services/qlnet/qlnet
    ↓
.pkgdir/qlnet/usr/bin/qlnet
    ├────────────────────────────→ STAGING_DIR_ROOT/usr/bin/qlnet
    │
    └→ ipkg-<arch>/qlnet/usr/bin/qlnet
          ↓ RSTRIP
       qlnet_*.ipk
          ↓ opkg
       TARGET_DIR/usr/bin/qlnet
```

对于 SDK Native RootFS：

```text
TARGET_DIR
    ↓
root.squashfs
```

对于当前 BBA：

```text
STAGING_DIR_ROOT
    ↓
supplier_fs_bin
    ↓
BBA FS_TG_PATH
    ↓
BBA root.squashfs
```

---

<a id="ch10"></a>
# 10. 阶段四：Recovery 与整机附属物料

本阶段处理普通 SDK RootFS 之外的 Recovery RootFS、Vendor Prebuilt、NV 和产品资源。

<a id="ch10-1"></a>
## 10.1 Recovery Image 配置

当前 v610：

```text
CONFIG_AB_SYSTEM is not set
```

`target/linux/unisoc/image/v610.mk` 的 Device 默认规则会加入：

```make
IMAGES += recovery.squashfs
IMAGE/recovery.squashfs := recovery-rootfs
```

因此当前 M8280 会生成独立 `recovery.squashfs`。

<a id="ch10-2"></a>
## 10.2 Recovery RootFS 组装

Recovery RootFS 工作目录：

```text
RECOVERY_ROOTFS_DIR=$(TARGET_DIR)/../recovery-unisoc
```

完整主链：

```text
make -C target/linux/unisoc/image install
    ↓
Build/recovery-rootfs
    ↓
make package/index
    ↓
创建 recovery-unisoc
    ↓
生成 recovery opkg.conf
    ↓
offline opkg update
    ↓
安装 libc_*.ipk
    ↓
安装 kernel_*.ipk
    ↓
安装 RECOVERY_PACKAGES
    ↓
prepare_rootfs
    ↓
裁剪非 Recovery 内容
    ↓
mksquashfs4
```

BBA 当前由：

```text
supplier_recovery_build
```

触发该 target。

<a id="ch10-3"></a>
## 10.3 Recovery Package Set

当前 `v610.mk` 固定：

```text
base-files
qlfota
swupdate
procd
busybox
logd
rawdata-tool
urngd
adbd
```

同时额外安装：

```text
libc_*.ipk
kernel_*.ipk
```

Recovery 是独立 Package RootFS，不是从 BBA `FS_TG_PATH` 复制出来的系统 RootFS。

<a id="ch10-4"></a>
## 10.4 `recovery.squashfs`

首次明确生成位置：

```text
$(KDIR)/recovery.squashfs
```

当前逻辑目录：

```text
build_dir/target-aarch64_cortex-a55_musl/
linux-unisoc_v610/recovery.squashfs
```

后续 Firmware Pack：

```text
find build_dir -name recovery.squashfs
    ↓
bin/unisoc/temp/recovery.squashfs
    ↓
CONFIG_ROOTFS_SECUREBOOT=y
    ↓
build_sign
    ↓
recovery-sign.squashfs
```

Gold Demo 已实机验证 Recovery 内存在 qlfota、swupdate、rawdata-tool、procd、logd、adbd 等关键组件。

<a id="ch10-5"></a>
## 10.5 Vendor Firmware 与产品物料

Firmware Packaging 还需要汇入多类不由普通 OpenWrt Package 产生的对象：

### AP / Secure Firmware

```text
sml.bin
teecfg.bin
tos.bin
UIS8510_SP.bin
ums9632_v610_adsp.bin
Project.bin
```

部分属于 Vendor Prebuilt，`build_fw()` / `build_fw_pack()` 将其复制进 Firmware Staging。

### Boot / Download Firmware

```text
fdl1.bin
u-boot-spl-16k.bin
fdl2.bin
u-boot.bin
sysdump.bin
boot.img
```

### NV / Product

```text
nvitem.bin
deltanv.bin
quectel_logo.bmp
Partition XML
```

这些对象与 `root.squashfs`、`recovery.squashfs` 一起构成整机 PAC Build 的输入。

---

<a id="ch11"></a>
# 11. 阶段五：Firmware 汇聚、签名与 PAC 输出

本章只覆盖 Build System 中从已生成物料到 PAC 的连接。PAC Item / Block / Flash 写入目标的详细定义由刷机指南维护。

<a id="ch11-1"></a>
## 11.1 整机物料汇聚

Gold `build_fw()` 与当前 BBA `build_fw_pack()` 都把整机输入集中到：

```text
sdk/ql_rg620ua/bin/unisoc/temp
```

其角色为：

```text
Boot output
Kernel output
RootFS
Recovery
Vendor firmware
NV / Product resources
Partition metadata
        ↓
bin/unisoc/temp
        ↓
Signing / CP Processing / PAC
```

当前 BBA 使用 external rootfs 时：

```text
platform/targets/M8280/EU/image/root.squashfs
    ↓
build_fw_pack(external_rootfs)
    ↓
bin/unisoc/temp/root.squashfs
```

<a id="ch11-2"></a>
## 11.2 AP / Boot 签名

`build_sign(image)` 的当前主流程：

```text
raw image
    ↓
imgheaderinsert
    ↓
sprd_sign sign_image
    ↓
signed image
```

当前 UIS8510 使用 RSA4096 签名路径；现有记录确认 `encrypt_flag=false`，因此该阶段按当前实现承担 SecureBoot authentication/signing，而不是普通 payload encryption。

RootFS SecureBoot 开启时：

```text
root.squashfs
    ↓
root-sign.squashfs

recovery.squashfs
    ↓
recovery-sign.squashfs
```

<a id="ch11-3"></a>
## 11.3 CP 固件处理

PAC 生成前：

```text
parser_ini.py
    ↓
cp_sign/<NWMODE>/pac.ini
    ↓
sign_cp.sh
    ↓
CP / Modem signed payload
```

UIS8510 NAND 继续执行：

```text
binary_gzip
```

该步骤处理需要进入 PAC 的 CP / Modem 类物料。详细 Item 与 Flash Block 映射不在本文重复。

<a id="ch11-4"></a>
## 11.4 PAC 打包链

当前链：

```text
Partitions / PAC Metadata
        +
AP / Boot signed images
        +
CP signed images
        +
RootFS / Recovery
        +
NV / Product resources
        ↓
parser_ini.py
        ↓
cp_sign/<NWMODE>/pac.ini
        ↓
sign_cp.sh
        ↓
binary_gzip
        ↓
makepac.py
        ↓
mkpac.pl
        ↓
*.pac
```

其中：

```text
makepac.py
```

负责 PAC Packaging Orchestration；

```text
mkpac.pl
```

是后续底层 PAC container packer。

PAC 私有 binary container format 不影响本文 Build 主链，不继续展开。

<a id="ch11-5"></a>
## 11.5 Release 输出

PAC 母体生成现场：

```text
bin/unisoc/temp/cp_sign/UIS8510_1H10_SEC/*.pac
```

随后进入：

```text
bin/target/RG258UB_GLABR01A01M4G/update/
```

BBA image 阶段再将对应 PAC 复制至：

```text
platform/targets/M8280/EU/image/
```

PAC 内部的下载项、Partition/Volume 映射和 QFlash 烧录流程见《M8280 / RG258UB_GLAB / UIS8510 / v610 完整刷机指南》。

<a id="ch11-6"></a>
## 11.6 SWU 分支状态

当前 BBA：

```text
build_fw_pack <BBA root.squashfs> fota
```

PAC 主链可以完成；`fota` 参数还会继续进入 SWU Generator。

当前 3.3.0 已确认 SWU Generator 与 BBA RootFS 的 `projectinfo` 路径存在兼容问题：

```text
SDK Tool 预期：
/etc/config/projectinfo

BBA RootFS：
/etc/config -> runtime /tmp/config_uci
默认种子位于 /etc/config_bak
```

该问题属于 OTA/SWU 专项，不影响本文 PAC Build 主链闭环。

---

<a id="ch12"></a>
# 12. BBA 3.3.0 SDK 接入机制

前 11 章建立 SDK 自身 Build 模型。本章集中描述 BBA 3.3.0 的 Supplier Adapter、Model Overlay、RootFS 分流和最终 Packaging 回接。

<a id="ch12-1"></a>
## 12.1 BBA 层级定位

BBA Build System 位于：

```text
M8280 / EU Product
        ↓
BBA Model
        ↓
BBA Build Orchestrator
        ↓
Supplier Adapter
        ↓
Quectel / Unisoc SDK
```

BBA 自身同时提供：

```text
public/private apps
public/private modules
filesystem
web / system files
product config
```

因此 BBA 的角色是 Product-level Build Orchestrator + SDK Adapter，不替代底层 OpenWrt / Kernel / Boot Build Framework。

<a id="ch12-2"></a>
## 12.2 Supplier Adapter

当前入口：

```text
platform/build/makes/Makefile.sdk.quecopen_rg620ua.mk
```

M8280 固定映射：

```text
QUECTEL_PROJECT_NAME = RG258UB_GLAB
QUECTEL_PROJECT_REV  = RG258UB_GLABR01A01M4G
QUECTEL_CUSTOM_NAME  = STD

KERNEL_SUBTARGET = v610
SDK_CONFIG_FILE   = sdk/.../config/defconfig_unisoc610_nand
KERNEL_CONFIG_FILE= sdk/.../target/linux/unisoc/v610/config-default-nand
PARTITION_FILE    = sdk/.../uis8510-1h10-nand-cpe.xml
PAC_INI_FILE      = sdk/.../uis8510-1h10-nand.ini
DTS_FILE          = sdk/.../kernel_6.6/.../uis8510-1h10-nand.dts
```

该 Makefile 定义 BBA 各阶段对 SDK target 的调用方式。

<a id="ch12-3"></a>
## 12.3 M8280 Model Overlay

当前主要 Overlay：

| BBA Model Source | SDK Destination | 当前作用 |
|---|---|---|
| `model/M8280/EU/config.sdk` | `config/defconfig_unisoc610_nand` | OpenWrt 产品配置 |
| `model/M8280/EU/config.kernel` | `target/linux/unisoc/v610/config-default-nand` | Kernel 配置 |
| `model/M8280/EU/dts/v610.dts` | `kernel_6.6/.../uis8510-1h10-nand.dts` | 产品 DTS |
| `model/M8280/EU/exfiles/kernel-build.mk` | `include/kernel-build.mk` | Kernel stage 调整 |
| `model/M8280/EU/exfiles/v610.mk` | `target/linux/unisoc/image/v610.mk` | Image / boot-img 调整 |
| `model/M8280/EU/exfiles/ql_build_config` | `quectel/unisoc/compile/ql_build_config` | Build 拆分与 external rootfs |
| `model/M8280/EU/partitions/*` | SDK PAC XML / INI | 当前产品 PAC / Partition delta |

New SDK rebase 后当前主要 Delta：

### `config.sdk`

当前以 Gold `defconfig_unisoc610_nand` 为 baseline。

### `config.kernel`

当前在 Gold baseline 上保留：

```text
CONFIG_UBIFS_FS_ZLIB=y
CONFIG_CRYPTO_DEFLATE=y
```

用于 BBA misc UBIFS ZLIB 支持。

### DTS

当前 BBA DTS 在 Gold 基础上保留 4 个产品 Delta：

```text
stdout-path : 921600 → 115200
earlycon    : 921600 → 115200
console     : 921600 → 115200
init        : /etc/preinit → /sbin/init
```

### `v610.mk`

Gold：

```text
KERNELNAME := Image dtbs
```

BBA：

```text
KERNELNAME := Image.gz dtbs
```

并增加 standalone `boot-img` target。

<a id="ch12-4"></a>
## 12.4 `ql_build_config` 拆分

Gold 原生：

```text
build_fw()
    ├─ OpenWrt make
    ├─ collect
    ├─ signing
    └─ PAC
```

当前 BBA Overlay：

```text
build_openwrt()
    └─ OpenWrt make

build_fw_pack()
    ├─ external_rootfs 支持
    ├─ collect
    ├─ signing
    ├─ PAC
    └─ fota 参数

build_fw()
    ├─ 清理
    ├─ build_openwrt
    └─ build_fw_pack
```

BBA 的分阶段 Build 不直接调用 wrapper `build_fw()`，而在前面各阶段分别构建 SDK 组件，在 `image_build` 中单独调用：

```text
build_fw_pack $(BBA_ROOTFS_SQUASHFS) fota
```

因此 BBA 可以在 OpenWrt Package Build 与 Firmware Pack 中间插入自己的 RootFS。

<a id="ch12-5"></a>
## 12.5 `env_build`

当前主要链：

```text
env_build
    ↓
supplier_env_pre
    ├─ config.sdk → SDK defconfig
    ├─ exfiles/ql_build_config → SDK ql_build_config
    └─ 其他当前 overlay
    ↓
supplier_env_build
    ↓
source ql_build_config
    ↓
buildconfig RG258UB_GLAB RG258UB_GLABR01A01M4G STD
    ↓
检查 v610 prebuilt host/toolchain
```

M8280 不执行旧：

```text
tools/compile
toolchain/compile
```

<a id="ch12-6"></a>
## 12.6 `boot_build`

当前：

```text
boot_build
    ↓
supplier_boot_build
    ↓
source ql_build_config
buildconfig ...
    ↓
package/boot/chipram4-unisoc/compile
    ↓
package/boot/uboot44-unisoc/compile
```

`buildconfig` 与 Boot target 位于同一个 recipe shell，用于保证 Boot Build 依赖的环境变量有效。

<a id="ch12-7"></a>
## 12.7 `kernel_build`

当前：

```text
kernel_build
    ↓
supplier_kernel_prepare
    ├─ config.kernel overlay
    ├─ v610.mk overlay
    └─ DTS overlay
    ↓
supplier_kernel_build
    ├─ make target/linux/{compile,install}
    └─ make -C target/linux/unisoc/image boot-img
```

当前 `supplier_kernel_build` 本身不重新调用 `buildconfig`。

其输入主要通过 SDK `.config` 和前置 Overlay 固化，而不是依赖该 recipe 内再次生成 Product shell 环境。

<a id="ch12-8"></a>
## 12.8 `modules_build`

当前：

```text
modules_build
    ↓
supplier_modules_build
    ├─ make package/kernel/linux/compile
    └─ make package/kernel/nat46/compile
```

同时 BBA 自己还有：

```text
public_modules_build
private_modules_build
```

三类 Module 体系必须分别识别：

```text
Kernel source module
SDK KernelPackage / supplier module
BBA public/private module
```

<a id="ch12-9"></a>
## 12.9 `apps_build`

BBA Apps 阶段同时包含：

```text
supplier_apps_build
public_apps_build
private_apps_build
tests
```

当前 `supplier_apps_build`：

```text
source ql_build_config
buildconfig ...
    ↓
显式 make package/.../compile
    ↓
make package/install
    ↓
make target/install
```

所以到 `apps_build` 完成时，SDK Package、STAGING_DIR_ROOT、IPK 和 SDK TARGET_DIR 均已经形成。

BBA public/private app 使用 BBA 自己的 Makefile 体系，不属于 SDK OpenWrt Package Framework。

<a id="ch12-10"></a>
## 12.10 `fs_build`

BBA 最终文件系统工作目录：

```text
FS_TG_PATH
=
platform/targets/M8280/EU/filesystem
```

`Makefile.rootfs`：

```text
fs_build: fs_clean $(FS_BUILD)
```

主要阶段：

```text
fs_clean
    ↓
fs_create
    ↓
fs_lib
    ↓
fs_bin
    ↓
fs_script
    ↓
fs_modules
    ↓
lang / system / web
    ↓
fs_check / fs_dev
    ↓
fs_strip / fs_strip_post
    ↓
fs_model_ver
    ↓
fs_rootfs
    ↓
fs_ver
```

### `fs_create`

基础模板：

```text
platform/targets/fs.dir
    ↓
FS_TG_PATH
```

并注入：

```text
model/M8280/EU/inittab
model/M8280/EU/rcS
model/M8280/EU/rcS.quecopen_rg620ua
model/M8280/EU/config.bba
```

### `fs_lib`

为最终设备补入 toolchain / libc Runtime，例如：

```text
ld-*.so*
lib*.so*
```

来源为 `SLIB_PATH`。

### `fs_bin`

当前接线：

```text
fs_bin:
    tests_pre_install
    supplier_fs_bin
    public_apps_install
    private_apps_install
    supplier_apps_install
    tests_post_install
```

### `fs_modules`

当前：

```text
public_modules_install
private_modules_install
supplier_modules_install
```

### `fs_sysfiles`

Model filesystem overlay：

```text
model/M8280/EU/filesystem/*
    ↓
FS_TG_PATH
```

同时加入 BBA Web 和其他系统资源。

<a id="ch12-11"></a>
## 12.11 BBA RootFS

当前 Supplier RootFS 输入：

```text
SUPPLIER_ROOTFS_PATH
=
sdk/ql_rg620ua/staging_dir/
target-aarch64_cortex-a55_musl/root-unisoc
```

也就是：

```text
SDK STAGING_DIR_ROOT
```

而不是 SDK `TARGET_DIR`。

当前主链：

```text
SDK Package Build
    ↓
.pkgdir
    ↓
STAGING_DIR_ROOT
    ↓
supplier_fs_bin 选择性 copy
        +
BBA public/private apps
        +
BBA modules
        +
BBA base filesystem
        +
Model overlay
        +
BBA Web / System files
    ↓
FS_TG_PATH
    ↓
fs_strip / fs_strip_post
    ↓
fs_quecopen_rootfs
    ↓
platform/targets/M8280/EU/image/root.squashfs
```

`fs_rootfs` 当前接线：

```text
fs_rootfs: fs_quecopen_rootfs
```

BBA `mksquashfs4` 使用 xz 压缩和当前 v610 SecureBoot RootFS 所需的 offset 参数。

SDK Native RootFS 与 BBA RootFS 的压缩参数、输入树和 Runtime 文件来源均不完全相同。

<a id="ch12-12"></a>
## 12.12 `image_build`

当前：

```text
image_build
    ↓
quecopen_image_build
    ├─ mkburning_build
    └─ mkupgrade_build
```

`mkupgrade_build` 当前为空实现。

`mkburning_build` 前置：

```text
supplier_recovery_build
quecopen_create_misc_ubifs
```

其中：

```text
supplier_recovery_build
    ↓
make -C target/linux/unisoc/image install
    ↓
recovery.squashfs
```

当前 misc 初始镜像：

```text
misc_ro.ubifs
misc_rw.ubifs
```

随后：

```text
source ql_build_config
buildconfig ...
    ↓
包装 build_pac()，在 PAC 前注入 misc UBIFS
    ↓
build_fw_pack \
    platform/targets/M8280/EU/image/root.squashfs \
    fota
```

因此 image 阶段是 BBA RootFS 与 SDK Firmware Packaging 的重新汇合点。

<a id="ch12-13"></a>
## 12.13 SDK RootFS 与 BBA RootFS 关系

当前存在两条不同的文件系统路径。

### SDK Native

```text
OpenWrt Package
    ↓
IPK
    ↓
opkg
    ↓
SDK TARGET_DIR
    ↓
SDK root.squashfs
    ↓
SDK Demo Firmware
```

### M8280 BBA

```text
OpenWrt Package
    ↓
.pkgdir
    ↓
SDK STAGING_DIR_ROOT
    ↓
supplier_fs_bin
    ↓
BBA FS_TG_PATH
    ↓
BBA root.squashfs
    ↓
build_fw_pack(external_rootfs)
    ↓
PAC
```

因此以下两个判断均不成立：

```text
SDK TARGET_DIR 有文件
→ BBA 最终设备一定有

SDK root.squashfs
→ M8280 BBA 最终 root.squashfs
```

M8280 最终 RootFS 的直接验证点是：

```text
platform/targets/M8280/EU/filesystem
```

以及随后生成的：

```text
platform/targets/M8280/EU/image/root.squashfs
```

---

<a id="ch13"></a>
# 13. BBA 3.3.0 全量构建阶段映射

<a id="ch13-1"></a>
## 13.1 顶层构建命令

当前典型构建：

```bash
cd platform/build

make SHELL=/bin/bash \
    MODEL=M8280 \
    SPEC=EU \
    env_build \
    boot_build \
    kernel_build \
    modules_build \
    apps_build \
    fs_build \
    image_build
```

BBA 顶层阶段：

```text
env
boot
kernel
modules
apps
fs
image
```

对应：

```text
env_build
boot_build
kernel_build
modules_build
apps_build
fs_build
image_build
```

<a id="ch13-2"></a>
## 13.2 阶段映射表

| BBA 阶段 | 当前 Supplier / SDK 动作 | 主要输出 |
|---|---|---|
| `env_build` | Model Overlay；`buildconfig`；检查 prebuilt host/toolchain | SDK `.config`、产品环境 |
| `boot_build` | `chipram4-unisoc/compile`；`uboot44-unisoc/compile` | FDL / SPL / U-Boot |
| `kernel_build` | `target/linux/{compile,install}`；standalone `boot-img` | Image.gz / DTB / boot.img / `.ko` |
| `modules_build` | `package/kernel/linux/compile`；`nat46/compile`；BBA modules | kmod / external module |
| `apps_build` | SDK Packages；`package/install`；`target/install`；BBA apps | IPK / STAGING_DIR_ROOT / TARGET_DIR / BBA binaries |
| `fs_build` | supplier runtime + BBA apps/modules/model/system/web；mksquashfs | BBA `root.squashfs` |
| `image_build` | recovery；misc UBIFS；`build_fw_pack(external_rootfs,fota)` | PAC；SWU 分支入口 |

当前以下 Supplier target 为空：

```text
supplier_kernel_install
supplier_modules_install
supplier_apps_install
supplier_mkkernel_build
supplier_image_build
```

不能根据 target 名称推断存在实际 recipe。

<a id="ch13-3"></a>
## 13.3 完整产物流

当前 M8280 BBA 全链：

```text
MODEL=M8280 / SPEC=EU
        ↓
model/M8280/EU
        ↓
env_build
        ↓
SDK config / ql_build_config overlay
        ↓
buildconfig RG258UB_GLAB ...
        ↓
OpenWrt .config / Device / Toolchain
        ↓
boot_build
        ├─ FDL1
        ├─ SPL
        ├─ FDL2
        └─ U-Boot
        ↓
kernel_build
        ├─ Linux 6.6 .config
        ├─ Image.gz
        ├─ DTB
        ├─ boot.img
        └─ Kernel .ko
        ↓
modules_build
        └─ KernelPackage / kmod / BBA modules
        ↓
apps_build
        ├─ SDK Package
        ├─ .pkgdir
        ├─ STAGING_DIR_ROOT
        ├─ IPK
        ├─ TARGET_DIR
        └─ BBA public/private app
        ↓
fs_build
        ├─ supplier_fs_bin
        ├─ BBA filesystem
        ├─ BBA apps/modules
        ├─ model overlay
        ├─ strip
        └─ BBA root.squashfs
        ↓
image_build
        ├─ recovery.squashfs
        ├─ misc_ro.ubifs
        ├─ misc_rw.ubifs
        ├─ build_fw_pack(BBA root.squashfs)
        ├─ signing
        ├─ CP processing
        └─ PAC
```

---

<a id="ch14"></a>
# 14. 增量构建、Stamp 与 Build Cache

Build Framework 通过 stamp、generated config 和各层工作目录支持增量构建。配置输入、工作目录状态和最终 Binary 必须分层验证。

<a id="ch14-1"></a>
## 14.1 Package Stamp

Package build_dir 常见：

```text
.prepared_*
.configured_*
.built
```

含义：

| Stamp | 表示状态 |
|---|---|
| `.prepared_*` | Prepare 已完成 |
| `.configured_*` | Configure 已完成 |
| `.built` | Build 阶段已完成 |

`.built` 不等于“编译器已经运行”。预编译 ELF Package 也可以在空 `Build/Compile` 后生成 `.built`。

<a id="ch14-2"></a>
## 14.2 Staging 记录

标准 `Build/InstallDev` 使用：

```text
staging_dir/.../packages/<package>.list
```

记录某 Package 向公共 STAGING_DIR 导出的文件。

重新 staging / clean 时：

```text
<package>.list
    ↓
scripts/clean-package.sh
    ↓
删除旧 staging 文件
```

Package 如果绕过标准 Framework 直接向 STAGING_DIR 写文件，则需要额外检查残留文件。

<a id="ch14-3"></a>
## 14.3 Kernel Build Cache

Kernel 配置修改应验证：

```text
BBA config.kernel
    ↓
SDK config-default-nand
    ↓
.config.target
    ↓
.config.override
    ↓
.config.set
    ↓
kernel_6.6/.config
    ↓
Image / .ko
```

只检查前两层不能证明 Kernel 最终配置值。

DTS 修改应验证：

```text
BBA dts/v610.dts
    ↓
SDK uis8510-1h10-nand.dts
    ↓
uis8510-1h10-nand.dtb
    ↓
boot.img
```

<a id="ch14-4"></a>
## 14.4 Boot Build Cache

U-Boot 已实机暴露过 Target build_dir 配置未随 source defconfig 自动刷新的情况。

验证链：

```text
source defconfig
    ↓
target u-boot44 build_dir/.config
    ↓
generated auto.conf / autoconf.h
    ↓
u-boot.bin
    ↓
signed U-Boot
    ↓
PAC
```

Host U-Boot build_dir 不属于目标板 U-Boot 证据。

<a id="ch14-5"></a>
## 14.5 Make Recipe Shell 环境

BBA 顶层各阶段是不同 Make target。`buildconfig` 在一个 recipe shell 中导出的 shell variable 不会自动成为另一个独立 recipe shell 的状态。

早期 M8280 Boot 问题已经证明：

```text
env_build 执行 buildconfig
```

不能自动保证：

```text
boot_build 的 recipe shell
```

仍然拥有完整 `SECBOOT_ENABLE / USERDEBUG / UNISOC_PRODUCT` 环境。

因此当前 Boot 和 Apps 等需要这类环境的 target，会在各自 recipe shell 中重新：

```text
source ql_build_config
buildconfig ...
```

当前已确认重新调用位置：

```text
supplier_env_build
supplier_boot_build
supplier_boot_clean
supplier_apps_build
supplier_apps_clean
mkburning_build
```

<a id="ch14-6"></a>
## 14.6 修改对象与重编范围

| 修改对象 | 主要刷新层 | 核心验证点 |
|---|---|---|
| `config.sdk` | OpenWrt `.config`、相关 Package/Kernel wrapper | SDK `.config` |
| `config.kernel` | Kernel configure / compile | `kernel_6.6/.config`、Image / `.ko` |
| DTS | Kernel dtbs + boot-img | `.dtb`、`boot.img` |
| U-Boot defconfig | uboot44 target build_dir | Target `.config`、generated config、`u-boot.bin` |
| Chipram source/config | chipram4 Package | FDL1 / SPL |
| Package source | Package Prepare/Compile/Package | PKG_BUILD_DIR、`.pkgdir`、IPK |
| Package `install` | `.pkgdir`、STAGING_DIR_ROOT、IPK | 各中间 payload |
| `Build/InstallDev` | STAGING_DIR | Header / Library |
| BBA app | BBA app build + install | app output、FS_TG_PATH |
| BBA filesystem | `fs_build` | FS_TG_PATH、BBA `root.squashfs` |
| Recovery rule/package set | image install / recovery-rootfs | `recovery-unisoc`、`recovery.squashfs` |
| PAC metadata | Firmware Pack | temp XML/INI、cp_sign PAC |

出现最终固件仍携带旧文件时，应从离源码最近的一级开始逐层比较，而不是直接重新全量编译。

---

<a id="ch15"></a>
# 15. 产物反查与源码索引

<a id="ch15-1"></a>
## 15.1 产物 Producer 索引

| 产物 | 主要 Producer / 入口 |
|---|---|
| `fdl1.bin` | `package/boot/chipram4-unisoc` / Chipram4 |
| `u-boot-spl-16k.bin` | Chipram4 / SPL |
| `fdl2.bin` | `package/boot/uboot44-unisoc` |
| `u-boot.bin` | `package/boot/uboot44-unisoc` |
| `Image` / `Image.gz` | `target/linux/compile` → Linux Kbuild |
| `uis8510-1h10-nand.dtb` | Linux `make dtbs` |
| `boot.img` | `target/linux/unisoc/image/v610.mk` → `mkkernelimg.py` |
| Kernel `.ko` | Linux `make ... modules` |
| `kmod-*.ipk` | `KernelPackage` / `BuildTarget/ipkg` |
| Userspace `*.ipk` | Package `BuildPackage` / `BuildTarget/ipkg` |
| SDK TARGET_DIR | `make package/install` / opkg |
| SDK `root.squashfs` | `include/image.mk` / mksquashfs4 |
| `recovery.squashfs` | `Build/recovery-rootfs` |
| BBA `root.squashfs` | `fs_quecopen_rootfs` |
| signed image | `build_sign()` / `sign_cp.sh` |
| PAC | `build_pac()` → `makepac.py` → `mkpac.pl` |

<a id="ch15-2"></a>
## 15.2 构建异常定位索引

| 现象 | 首要层级 | 关键对象 |
|---|---|---|
| Project 映射错误 | 产品配置 | `ql_build_config` / `ql_build_product` |
| Package 未进入 Build | Package 选择 | defconfig → `.config` → `.packagedeps` |
| Package compile 成功但无 IPK | Package Pack | `.pkgdir` → IPKG IDIR → `bin/packages` |
| IPK 存在但 SDK RootFS 缺文件 | SDK RootFS | `pkginfo` → `opkg_install_list` → TARGET_DIR |
| BBA 设备缺少 SDK 文件 | BBA RootFS | STAGING_DIR_ROOT → `supplier_fs_bin` → FS_TG_PATH |
| Header / Library 找不到 | Target Sysroot | `Build/InstallDev` → STAGING_DIR |
| Kernel 宏值异常 | Kernel config | `.config.target` / `.override` / `.set` / final `.config` |
| `.ko` 不生成 | Linux module compile | `CONFIG_xxx=m` / `.modules` |
| kmod 不进 RootFS | KernelPackage / Package install | `CONFIG_PACKAGE_kmod-*` / IPK / TARGET_DIR |
| DTS 修改未进固件 | DTS / boot-img | DTS → DTB → `boot.img` |
| U-Boot config 修改未生效 | Boot cache | Target U-Boot `.config` / generated config |
| Recovery 未生成 | Recovery image | `supplier_recovery_build` / `recovery-rootfs` |
| PAC 使用旧 RootFS | BBA image | BBA `root.squashfs` → temp → signed rootfs → PAC |
| PAC 已生成但 Release 未更新 | Release copy | `bin/unisoc/temp/cp_sign` → `bin/target/<REV>` |

<a id="ch15-3"></a>
## 15.3 核心源码入口

### 产品配置

```text
sdk/ql_rg620ua/quectel/unisoc/compile/ql_build_config
sdk/ql_rg620ua/quectel/unisoc/compile/ql_build_product
sdk/ql_rg620ua/config/defconfig_unisoc610_nand
```

### OpenWrt Framework

```text
sdk/ql_rg620ua/rules.mk
sdk/ql_rg620ua/include/package.mk
sdk/ql_rg620ua/include/package-pack.mk
sdk/ql_rg620ua/include/rootfs.mk
sdk/ql_rg620ua/include/kernel.mk
sdk/ql_rg620ua/include/kernel-build.mk
sdk/ql_rg620ua/include/kernel-defaults.mk
sdk/ql_rg620ua/include/image.mk
```

### Kernel / Device / Image

```text
sdk/ql_rg620ua/target/linux/unisoc/Makefile
sdk/ql_rg620ua/target/linux/unisoc/v610/config-default-nand
sdk/ql_rg620ua/target/linux/unisoc/image/v610.mk
sdk/ql_rg620ua/target/linux/unisoc/image/mkkernelimg.py
sdk/ql_rg620ua/unisoc/linux/kernel_6.6/
sdk/ql_rg620ua/unisoc/linux/kernel_6.6/arch/arm64/boot/dts/sprd/uis8510-1h10-nand.dts
```

### Kernel Module

```text
sdk/ql_rg620ua/package/kernel/linux/Makefile
sdk/ql_rg620ua/package/kernel/linux/modules/
sdk/ql_rg620ua/package/kernel/linux/modules/netfilter.mk
sdk/ql_rg620ua/package/kernel/nat46/Makefile
```

### Package

```text
sdk/ql_rg620ua/feeds/
sdk/ql_rg620ua/package/feeds/
sdk/ql_rg620ua/quectel/services/
```

qlnet 实例：

```text
sdk/ql_rg620ua/feeds/quectel_services/qlnet/Makefile
sdk/ql_rg620ua/quectel/services/qlnet/src/qlnet
```

### Firmware Packaging

```text
sdk/ql_rg620ua/quectel/unisoc/compile/ql_build_config
sdk/ql_rg620ua/unisoc/prebuilts/pac_script/parser_ini.py
sdk/ql_rg620ua/unisoc/prebuilts/pac_script/makepac.py
sdk/ql_rg620ua/unisoc/prebuilts/pac_script/mkpac.pl
sdk/ql_rg620ua/unisoc/prebuilts/scripts/packimage_scripts/sign_cp.sh
```

### BBA

```text
platform/build/Makefile
platform/build/makes/Makefile.sdk.quecopen_rg620ua.mk
platform/build/makes/Makefile.rootfs
platform/build/makes/Makefile.apps.public
platform/build/makes/Makefile.apps.private
platform/build/makes/Makefile.kmod.public
platform/build/makes/Makefile.kmod.private
platform/build/model/M8280/EU/
platform/targets/M8280/EU/filesystem
platform/targets/M8280/EU/image
```

<a id="ch15-4"></a>
## 15.4 当前证据边界

以下项目不影响当前 Build 主链，但在相关专项中仍保留边界：

1. Gold 原生 `KERNELNAME := Image dtbs` 与 `Build/make-boot-img` 读取 `Image.gz` 之间的原生 Image.gz 生成保证未在旧 Node 6 单独定位；当前 BBA 已通过 `Image.gz dtbs` 明确处理。
2. Recovery `cp $(KDIR)/recovery.squashfs $@` 的最终 OpenWrt image 副本路径未作为 PAC 依赖展开；当前 PAC 直接从 `build_dir` 搜索 `recovery.squashfs`。
3. `LINUX_UNAME_VERSION` 的具体字符串属于每次 Kernel 构建结果，本文不冻结动态值。
4. SWU Generator 当前仍存在 BBA `projectinfo` 路径兼容问题；PAC Build 和实机启动闭环不受该项影响。
5. PAC 私有容器内部格式、QFlash / FDL2 运行时烧录实现属于刷机专项。

---

<a id="appendix-a"></a>
# 附录 A. 核心数据源

本文主线由以下当前和专项资料交叉整理：

```text
M8280-RG258UB_GLAB-UIS8510-v610-NewSDK_Gold_BBA3.3.0_Rebase与首烧启动闭环_20260904.txt

M8280-RG258UB_GLAB-UIS8510-v610
3.3.0 当前工程路径与数据源优先级增量记录.txt

v610_SDK配置与BBA适配机制总结_2026-08-13.docx

v610-UIS8510-M8280 第一阶段第六节：
DTS-DTB Build 链.txt

v610 SDK Build System — Node 7：
OpenWrt Package 构建与 RootFS 安装机制.txt

v610-M8280 SDK Build System — Node 8：
build_dir-staging_dir-bin 目录与产物流转.txt

[NODE 9 — RootFS-最终文件系统组装 — CLOSED].txt

M8280-RG258UB_GLAB-UIS8510-v610
Phase 1-Node 10：Image-SecureBoot-PAC 最终打包链.txt

BBA3.0 上层 Build System 通用构建机制与源码导航.txt

M8280-RG258UB_GLAB-UIS8510-v610_完整刷机指南 2.md
```

2026-09-10 对 Gold、当前 BBA、Kernel Module、Recovery 和 `Makefile.rootfs` 的补充源码闭环用于更新以下主干：

```text
Gold buildconfig / build_fw
BBA supplier target → SDK target 映射
Kernel .ko → KernelPackage
Recovery RootFS → recovery.squashfs
fs_bin / fs_rootfs 接线
```

---

# 结论

当前 M8280 Build System 可以归纳为两层连续体系：

```text
第一层：Quectel / Unisoc v610 SDK

Product / defconfig
    ↓
OpenWrt Build Framework
    ↓
Boot / Kernel / Module / Package
    ↓
SDK RootFS / Recovery
    ↓
Firmware Assembly / Signing / PAC
```

```text
第二层：BBA 3.3.0 Product Build

MODEL / SPEC
    ↓
Model Overlay + Supplier Adapter
    ↓
分阶段调用 SDK
    ↓
BBA apps / modules / filesystem
    ↓
BBA RootFS
    ↓
重新进入 SDK Firmware Packaging
    ↓
PAC
```

当前 M8280 最关键的 Build 边界为：

```text
SDK .config
!= Linux Kernel .config

Linux .ko 编译
!= KernelPackage 打包

Package compile
!= Package 已进入 RootFS

STAGING_DIR_ROOT
!= TARGET_DIR

SDK Native root.squashfs
!= BBA Final root.squashfs

Gold SDK build_fw
!= BBA 拆分后的 build_openwrt + build_fw_pack
```

沿这些边界进行源码、配置、产物和日志定位，可以把大多数构建问题收敛到明确的 Producer、Build Stage 和输出目录。
