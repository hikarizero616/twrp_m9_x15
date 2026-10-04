# TWRP Device Tree for alps m9_x15 (`k53_cb_m1_x15`)

[![Build TWRP 8.1 for m9_x15](https://github.com/hikarizero616/twrp_m9_x15/actions/workflows/build-twrp.yml/badge.svg)](https://github.com/hikarizero616/twrp_m9_x15/actions/workflows/build-twrp.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Device configuration tree for building TeamWin Recovery Project (TWRP) for the **alps m9_x15** Android MP4 Player / PMP (board: `k53_cb_m1_x15`, MediaTek MT6753 / MT6735).

---

## ⚠️ 免责声明 / Disclaimer

> [!CAUTION]
> **刷机与修改底层分区存在风险。**
> 修改设备分区或刷写第三方 Recovery 可能导致设备保修失效、数据丢失，甚至导致设备无法开机（变砖）。
> 本项目代码按“原样”（AS-IS）提供，不包含任何明示或暗示的保证。对于因使用本仓库代码而造成的任何直接或间接损失，维护者与贡献者概不承担责任。请在操作前务必完整备份关键底层分区（如 `nvram`, `protect1`, `protect2`, `boot`, `recovery`）。

---

## 中文说明

### 设备规格概览

| 项目 | 参数 |
|---|---|
| 设备类型 | 安卓智能 MP4 随身播放器 / Portable Media Player (PMP) |
| 设备型号 | alps m9_x15 |
| 主板代号 | `k53_cb_m1_x15` |
| 芯片平台 | MediaTek MT6753 (内核报告 `ro.hardware=mt6735`) |
| 架构 | arm64 (AArch64) |
| 原厂底包版本 | Android 8.1.0 Oreo |
| Recovery 分区上限 | 24 MiB (`25,165,824` 字节) |
| Recovery 底包 | Android 8.1 基础构建环境 + TWRP 3.7.0 (android-9.0 recovery 源码) |
| 外置存储 | MicroSD / TF 卡扩展 (`/external_sd`)，支持 USB-OTG |

### MP4 设备适配要点

1. **屏幕尺寸与 UI 缩放**：
   - 作为便携触屏 MP4，屏幕尺寸一般在 3.5 ~ 5.0 英寸左右。
   - 当前预设为 `TW_THEME := portrait_hdpi` + `TARGET_SCREEN_DENSITY := 240`。
   - 若上机后发现按钮字体过大、界面溢出或截断，可将 [`BoardConfig.mk`](BoardConfig.mk) 中的主题切换为 `TW_THEME := portrait_mdpi`，并将密度调整为 `160` 或 `200`。
2. **MicroSD / TF 卡挂载**：
   - MP4 播放器日常刷机与媒体存放主要依赖 TF 卡。`recovery.fstab` 中已规范配置 `/external_sd` 挂载参数（`storage;wipeingui;removable`），TWRP 界面内点击「选择存储器」可直接读取外置 TF 卡。
3. **无蜂窝基带特性**：
   - 该设备为纯无线多媒体播放设备，无 SIM 模块与蜂窝基带。
4. **USB 与充电**：
   - `init.recovery.mt6735.rc` 中配置了 USB 插入检测机制，进入 Recovery 时会自动拉高 USB 电源并启动 adbd 服务，保障小电池容量下的调试续航。

### 内核与 GPLv2 合规说明

* 本设备树采用预编译内核二进制 [`prebuilt/kernel`](prebuilt/kernel)，格式为 MediaTek 典型的 **`Image.gz-dtb`**（`gzip(arm64 Image) + 51,895 B 附加设备树 DTB`），内核版本为 **Linux 3.18.79**。
* **GPLv2 开源说明**：Linux 内核基于 GNU GPLv2 许可证。本仓库包含的预编译内核直接提取自原厂出厂固件镜像，仅用于设备非商业兼容性测试。如需内核源代码，可参考 MediaTek 对应平台开放源码或联系硬件供应商获取对应 BSP 源码。
* **内核校验工具**：刷机前强烈建议使用内置工具核对提取自设备的 `boot.img` 或 `recovery.img`：
  ```bash
  # 校验本机提取镜像与预编译内核是否一致
  python3 tools/compare-kernel.py recovery.img
  ```

### 安全与调试配置说明

1. **Permissive SELinux**：[`BoardConfig.mk`](BoardConfig.mk) 中配置了 `androidboot.selinux=permissive`，以便 TWRP 在缺乏专有 sepolicy 规则的情况下正常挂载与执行维修操作。
2. **防回滚时间戳 (2099-12-31)**：`PLATFORM_SECURITY_PATCH` 与 `VENDOR_SECURITY_PATCH` 设为 `2099-12-31`，系用于避开 MTK 引导程序的防回滚版本校验机制。

### 构建指南

#### 方式一：GitHub Actions 自动构建
直接在 GitHub 仓库的 **Actions** 标签页选择 **Build TWRP 8.1 for m9_x15**，点击 **Run workflow**。构建完成后可在 Artifacts 下载生成的 `recovery.img`。

#### 方式二：本地构建
```bash
# 1. 准备并同步 TWRP 8.1 清单
mkdir -p ~/twrp && cd ~/twrp
repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_omni.git -b twrp-8.1
repo sync -j$(nproc) --force-sync --no-clone-bundle --no-tags

# 2. 放置本设备树
mkdir -p device/alps/k53_cb_m1_x15
cp -r /path/to/twrp_m9_x15/* device/alps/k53_cb_m1_x15/

# 3. 开始编译
source build/envsetup.sh
export ALLOW_MISSING_DEPENDENCIES=true
lunch omni_k53_cb_m1_x15-eng
mka recoveryimage -j$(nproc)
```

---

## English Overview

### Specifications

* **Device Type**: Android Portable Media Player (PMP / MP4)
* **Device Model**: alps m9_x15
* **Board**: `k53_cb_m1_x15`
* **SoC**: MediaTek MT6753 / MT6735
* **Base OS**: Android 8.1 Oreo
* **Recovery Partition**: 24 MiB (`25,165,824` bytes)
* **TWRP Base**: Minimal TWRP 8.1 manifest with TWRP 3.7.x recovery engine
* **Storage**: Internal eMMC + MicroSD (TF card) expansion + USB-OTG

### MP4 Form Factor Notes

* **Screen Scaling**: Given the compact touchscreen dimensions typical of Android MP4 players, if UI elements appear oversized with `portrait_hdpi`, switch `TW_THEME` to `portrait_mdpi` and set `TARGET_SCREEN_DENSITY` to `160` or `200` in [`BoardConfig.mk`](BoardConfig.mk).
* **MicroSD Mount**: Configured as `/external_sd` with proper storage flags for easy access in TWRP's Install and Backup screens.

### Kernel & GPLv2 Notice

* The binary at [`prebuilt/kernel`](prebuilt/kernel) is a stock prebuilt `Image.gz-dtb` blob (Linux **3.18.79**), extracted from stock firmware for non-commercial compatibility research.
* Linux is licensed under **GPLv2**. For kernel source code, please refer to MediaTek's open source portal or the device manufacturer.
* You can verify the kernel blob against your device's stock dump using:
  ```bash
  python3 tools/compare-kernel.py stock_recovery.img
  ```

---

## 开源许可证 / License

本设备树配置代码遵循 [Apache License 2.0](LICENSE) 许可证授权。
预编译内核二进制文件的使用需遵守其原始上游（Linux Kernel GPLv2）许可证条款。
