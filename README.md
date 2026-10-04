# TWRP device tree for alps m9_x15 (`k53_cb_m1_x15`)

Custom recovery (TWRP) device tree for the MTK **m9_x15** tablet, board codename
`k53_cb_m1_x15`, sold with Android 8.1 (fingerprint
`alps/full_k53_cb_m1_x15/k53_cb_m1_x15:8.1.0/O11019/1716970408:user/test-keys`).

```
#
# Copyright (C) 2026 The Android Open Source Project
# Copyright (C) 2026 SebaUbuntu's TWRP device tree generator
#
# SPDX-License-Identifier: Apache-2.0
#
```

---

## English

### What this tree actually builds

The workflow name says "TWRP 8.1", but the manifest branch only refers to the
**AOSP base**. `repo init -b twrp-8.1` resolves to:

| Project | Revision | Meaning |
| --- | --- | --- |
| `bootable/recovery` | TeamWin `android-9.0` | TWRP **3.7.0_9** (see `TW_MAIN_VERSION_STR`) |
| `build/make` | TeamWin `android-8.1` | build system |
| `vendor/omni` | TeamWin `android-8.1` | Omni/TWRP product config |

So the output is a **TWRP 3.7.x recovery built on an Android 8.1 base**.

### Kernel

No kernel source is compiled. `prebuilt/kernel` is a prebuilt blob:

* `Android Image.gz-dtb` style container: `gzip(arm64 Image) + 51,895 B appended DTB`
* Linux **3.18.79**, built `#1 SMP PREEMPT Wed May 29 …` with Linaro GCC 6.3.1
* It is picked up because `TARGET_PREBUILT_KERNEL` is set and
  `TARGET_KERNEL_SOURCE` (`kernel/alps/k53_cb_m1_x15`) does not exist — see
  `vendor/omni/build/tasks/kernel.mk`. `TARGET_FORCE_PREBUILT_KERNEL` is *not*
  consumed by the build system and only kept for documentation.

**Before flashing, verify the blob against your device's own image** (the tablet
may ship different kernel revisions):

```sh
# dump the stock boot/recovery image from the device first, then:
python3 tools/compare-kernel.py boot.img recovery.img
```

The script parses the Android boot header, unwraps the gzip container, splits the
appended DTB and compares SHA-256 of the raw blob, of the inner arm64 Image and of
the DTB separately, so you can tell "same kernel, repacked" from "different kernel".
Exit code is non-zero if anything differs. `--extract stock-kernel.bin` dumps the
kernel section if you want to use it instead.

### Partition budget

`recovery.img` must fit `BOARD_RECOVERYIMAGE_PARTITION_SIZE` (24 MiB). The last
successful CI build produced ~21.5 MB, so there are only ~3.6 MB of head room. The
workflow fails the build if the image grows past the limit.

### Known limitations

* **No `TW_INCLUDE_CRYPTO`** — encrypted `/data` (FBE/FDE) cannot be decrypted, only
  formatted (`Format Data`). Typical for unencrypted MTK 8.1 devices.
* **Screen density** — `TARGET_SCREEN_DENSITY := 240` with `TW_THEME := portrait_hdpi`
  is unverified; MTK stores panel timings in LK, not in the appended DTB, so the
  resolution could not be confirmed offline. If the UI is too large/small, try
  `portrait_mdpi` or another density.
* **`/persistent`** is mapped to `by-name/frp` (inherited from the stock fstab).
  It mounts, but the mapping is unusual — remove it if you do not need it.
* **Anti-rollback hack** — `PLATFORM_SECURITY_PATCH` / `VENDOR_SECURITY_PATCH` are
  set to `2099-12-31` and `PLATFORM_VERSION := 16.1.0`. These bogus values are
  intentional (see the comment in `BoardConfig.mk`); do not "fix" them.
* Unlocked bootloader required; Secure Boot/verity behaviour is device dependent.

### Building

Push to any branch (or run the workflow manually via *Actions → Run workflow*).
The workflow syncs the manifest, copies this tree to `device/alps/k53_cb_m1_x15`,
runs `mka recoveryimage` with ccache and uploads `recovery.img` as an artifact.

Local build:

```sh
mkdir -p ~/twrp && cd ~/twrp
repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_omni.git -b twrp-8.1
repo sync -j$(nproc)
mkdir -p device/alps/k53_cb_m1_x15
cp -r /path/to/twrp_m9_x15/* device/alps/k53_cb_m1_x15/
source build/envsetup.sh
export ALLOW_MISSING_DEPENDENCIES=true
lunch omni_k53_cb_m1_x15-eng
mka recoveryimage -j$(nproc)
```

Flash with `fastboot flash recovery out/target/product/k53_cb_m1_x15/recovery.img`
(or `dd` to the `recovery` partition).

### Layout

```
BoardConfig.mk                        board/kernel/fstab/TWRP config
device.mk                             device specific product bits
omni_k53_cb_m1_x15.mk                 product makefile (lunch target)
recovery.fstab                        partition table used by the recovery
recovery/root/init.recovery.mt6735.rc USB/charging init hooks
recovery/root/ueventd.rc              uevent rules
prebuilt/kernel                       prebuilt Image.gz-dtb (Linux 3.18.79)
tools/compare-kernel.py               verify the blob against a stock image
```

`extract-files.sh` / `setup-makefiles.sh` were removed: they required a
`proprietary-files.txt` and `tools/extract-utils/` that neither exist in this tree
nor are part of the `twrp-8.1` manifest. No proprietary blobs are copied — the
prebuilt kernel is the only binary.

---

## 中文

### 这个设备树实际构建的是什么

工作流名字写的是 "TWRP 8.1"，但那个 8.1 只是 **AOSP 底包版本**。
`repo init -b twrp-8.1` 实际解析为：`bootable/recovery` 取 TeamWin 的 **android-9.0**
分支（即 **TWRP 3.7.0_9**），`build/make` 与 `vendor/omni` 取 android-8.1。
所以产物是「Android 8.1 底包 + TWRP 3.7.x」。

### 内核

不从源码编译，直接用 `prebuilt/kernel`：格式是 **Image.gz-dtb**
（`gzip(arm64 Image) + 51,895 B 附加 DTB`），版本 **Linux 3.18.79**
（`#1 SMP PREEMPT Wed May 29 …`，Linaro GCC 6.3.1）。
它生效的原因是 `TARGET_PREBUILT_KERNEL` 已定义、而 `TARGET_KERNEL_SOURCE`
指向的内核源码树不存在（见 `vendor/omni/build/tasks/kernel.mk`）。
`TARGET_FORCE_PREBUILT_KERNEL` 其实没有任何代码消费，仅作注释保留。

**刷机前建议核对内核**：先 dump 本机的 boot/recovery 镜像，然后运行

```sh
python3 tools/compare-kernel.py boot.img recovery.img
```

脚本会解析 boot 头、解开 gzip、分离附加 DTB，分别对比原始 blob、内部 arm64 Image、
DTB 的 SHA-256，从而区分「同一个内核被重新打包」和「内核不同」。有差异时返回非 0。
加 `--extract stock-kernel.bin` 可导出原厂内核段以便替换。

### 分区容量

`recovery.img` 必须小于 24 MiB（`BOARD_RECOVERYIMAGE_PARTITION_SIZE`）。
上次成功构建约 21.5 MB，余量仅约 3.6 MB；工作流会在超出时直接让构建失败。

### 已知限制

* **未启用 `TW_INCLUDE_CRYPTO`**：无法解密加密的 `/data`（只能「格式化 Data」）。
* **屏幕密度未验证**：`TARGET_SCREEN_DENSITY := 240` + `TW_THEME := portrait_hdpi`；
  MTK 的面板参数存在 LK 里，无法离线确认。UI 不合适就换 `portrait_mdpi` 或改密度。
* **`/persistent` 映射到 `by-name/frp`**：沿用原厂 fstab，能挂但语义奇怪，不需要可删。
* **防回滚 hack**：`PLATFORM_SECURITY_PATCH` / `VENDOR_SECURITY_PATCH` 为 `2099-12-31`、
  `PLATFORM_VERSION := 16.1.0`，是刻意为之（见 `BoardConfig.mk` 注释），不要「修正」。
* 需解锁 bootloader；Secure Boot/verity 行为视机型而定。

### 构建

向任意分支 push 即触发（也可在 Actions 里手动 Run workflow）。CI 会同步清单、
把本设备树拷到 `device/alps/k53_cb_m1_x15`、带 ccache 执行 `mka recoveryimage`，
并上传 `recovery.img` 作为 artifact。

本地构建与刷入方式见上方英文部分（命令完全相同）。

### 目录结构

见上方英文部分的表格。已删除 `extract-files.sh` / `setup-makefiles.sh`：
它们依赖本仓库不存在的 `proprietary-files.txt` 和 `tools/extract-utils/`
（该目录在 `twrp-8.1` 清单中也不存在），属于无效代码；本设备树不需要拷贝专有库，
唯一的二进制就是预编译内核。
