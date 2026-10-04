# twrp_m9_x15 项目检查报告

检查日期：2026-10-04 ｜ 检查分支：`arena/01a107e9-twrp-m9-x15`（基于 `master` @ `6aa6e6f`）

> 说明：本报告是**审查基线**。审查后已按结论实施了一批修正，见文末「五、本次已实施的改动」。

---

## 一、项目概览

| 项 | 值 |
|---|---|
| 设备 | `alps m9_x15`（代号 `k53_cb_m1_x15`） |
| 平台 | `TARGET_BOARD_PLATFORM := mt6753`；内核 `ro.hardware=mt6735`（原厂 DTB 实测，见下） |
| 原厂系统 | Android 8.1.0（fingerprint `alps/full_k53_cb_m1_x15/...8.1.0/O11019/...`） |
| 内核 | 预编译 `prebuilt/kernel`（6.92 MB），不从源码编译 |
| 文件数 | 14 个，仅 1 个 squash 提交（历史不可追溯） |
| CI | GitHub Actions，`workflow_dispatch` 手动触发，产物 `TWRP-m9_x15-recovery` |

**一个重要澄清**：工作流名字叫 "Build TWRP 8.1"，但 `repo init -b twrp-8.1` 清单实际指向：

- `bootable/recovery` → TeamWin 的 **android-9.0** 分支（当前代码里 `TW_MAIN_VERSION_STR = "3.7.0_9"`，即 TWRP 3.7.0）
- `build/make` → TeamWin 的 android-8.1 分支
- `vendor/omni` → TeamWin 的 android-8.1 分支

所以这是「8.1 底包 + TWRP 3.7 时代 recovery 源码」，不是 TWRP 8.1。

CI 历史（master）：1 次取消、4 次失败、1 次成功（15 天前，耗时 11m24s，产物 zip 21,472,391 B）。
另有一个别的会话分支 `arena/01a107da-twrp-m9-x15` 的 push 触发构建仍在进行中，与本分支无关。

---

## 二、已核实正确的部分 ✅

1. **BoardConfig 里所有 TWRP 变量都真实存在**（对照实际使用的 recovery 源码逐条 grep）：
   `TW_THEME`（`gui/theme/portrait_hdpi` 存在）、`TW_SCREEN_BLANK_ON_BOOT`、`TW_INPUT_BLACKLIST`、`TW_EXTRA_LANGUAGES`、`TW_USE_TOOLBOX`。没有拼错的无效变量。
2. **fstab 与 rc 文件确实会被打包生效**：
   - `recovery.fstab` 放在设备树根目录会被自动采用（build/core/Makefile:1170 通配 `$(TARGET_DEVICE_DIR)/recovery.fstab`）；
   - `recovery/root/*` 会整体拷进 recovery ramdisk（同文件 :1156）；
   - `ueventd.rc` 会被 `/ueventd.rc` 读取（AOSP 8.1 `init/ueventd.cpp:230`），其 `subsystem/devname/dirname` 语法与 AOSP 自带 ueventd.rc 完全一致，合法。
3. **预编译内核的包装链路已确认走通**（这是最容易搞不清的一环）：
   `build/core/Makefile:3161` 的 `-include vendor/*/*/build/tasks/*.mk` → `vendor/omni/build/tasks/kernel.mk`；
   由于 `TARGET_KERNEL_SOURCE=kernel/alps/k53_cb_m1_x15` 在源码树中不存在，且 `TARGET_PREBUILT_KERNEL` 已定义，走 `KERNEL_BIN := $(TARGET_PREBUILT_KERNEL)`，然后原样 `cp` 到 `out/.../kernel`，最终由 mkbootimg `--kernel` 打进 recovery.img。
   （结论：`TARGET_FORCE_PREBUILT_KERNEL` 在这套构建里其实没人消费，是装饰性的；`BOARD_KERNEL_IMAGE_NAME` 只在从源码编译时起作用。）
4. **`androidboot.hardware=mt6735` 存在**：解析 `prebuilt/kernel` 尾部 DTB 得到
   `/chosen/bootargs = "console=tty0 console=ttyMT0,921600n1 root=/dev/ram initrd=0x44000000,0x300000 loglevel=8 androidboot.hardware=mt6735"`。
   这说明 `init.recovery.mt6735.rc` 能被加载（`TARGET_BOARD_PLATFORM=mt6753` 与 `ro.hardware=mt6735` 并存是 MTK 正常现象）。
5. **分区容量未超限**：recovery 分区上限 24 MiB（25,165,824 B）；CI 产物 zip 21,472,391 B（内核与 ramdisk 本身都是压缩数据，zip 大小≈镜像大小），余量约 3.6 MB —— 能刷，但偏紧。
6. 路径/命名一致：`DEVICE_PATH`、workflow 里的拷贝路径 `device/alps/k53_cb_m1_x15`、`AndroidProducts.mk` 与 `lunch omni_k53_cb_m1_x15-eng` 都对得上。

---

## 三、需要注意的问题（按重要性）

### P1 ⚠️ 内核 blobs 的格式与声明不一致，必须真机验证
`prebuilt/kernel` 不是裸的 `Image`，实际内容为：

```
gzip 流（解压后 16,310,312 B 的 arm64 Image，0x38 处有 "ARMd" 魔数）
+ 尾部 51,895 B 的 DTB（0xd00dfeed）  ← 即典型的 Image.gz-dtb
```

   而 BoardConfig 写的是 `BOARD_KERNEL_IMAGE_NAME := Image`。由于用预编译内核，这个变量不影响打包（见上），**但镜像里装的就是「gzip 内核 + 附加 DTB」**，能不能启动取决于该机 LK 是否自行解压。

   > 后续补充（解析内核镜像得到）：实际内核为 **Linux 3.18.79**，`#1 SMP PREEMPT Wed May 29 …`，
   > 编译者 `fox@ubuntu123`，Linaro GCC 6.3.1。构建日期与 ROM fingerprint 里的时间戳
   > `1716970408`（2024-05-29）一致，说明这个内核应与该 ROM 同批产出，但仍建议按上述方法逐字节核对。

- 验证方法：用 `unpackbootimg` 拆原厂 `boot.img`/`recovery.img`，把它的 kernel 段与 `prebuilt/kernel` 逐字节比对。
  - 若完全一致 → 原厂就是这么打包的，可行；
  - 若不一致 → 换成解压后的裸 `Image`（注意 DTB 要按 MTK 要求附带）。
- 另外把变量名统一（`Image.gz-dtb`）并加注释，能避免以后看日志误解。

### P2 构建不可复现
manifest 与各项目都跟**分支头**（`android-9.0`/`android-8.1`/`twrp-8.1`），没有固定 SHA，也没有 `repo` 快照。同一次 workflow 今天和明年跑出来的可能是不同代码。建议固定 revision 或改用带锁定的 manifest。

### P3 `extract-files.sh` / `setup-makefiles.sh` 是死代码
两脚本都引用 `proprietary-files.txt`（本仓库不存在），且依赖 `tools/extract-utils/extract_utils.sh`；而 `twrp-8.1` 清单里**没有** `tools/extract-utils`（这两个脚本是从新版 Lineage 模板复制来的）。直接运行必然报错。本设备树用预编译内核、不拷贝 vendor 库，所以它们没有用途 —— 建议删除或补上对应文件。

> 顺带说明：因为没有启用 `TW_INCLUDE_CRYPTO`，构建出的 TWRP **无法解密** FBE/加密的 `/data`（只能格式化）。MTK 8.1 机型大体如此，属已知限制，建议在 README 里写明。

### P4 BoardConfig 的两处历史遗留写法
- `VENDOR_SECURITY_PATCH` 定义了**两次**（`2021-08-01` 被后面的 `2099-12-31` 覆盖），第一行是死配置；
- `PLATFORM_VERSION := 16.1.0` + 2099 的安全补丁日期是常见的「防回滚」hack，功能上刻意为之，但没有任何注释。

建议删掉失效行并加注释，否则日后维护极易踩坑。

### P5 CI 配置可以更好
- 只有 `workflow_dispatch`（手动）；push/PR 不会触发（`arena/01a107da-...` 那个分支倒是加了 push 触发）；
- 没有 ccache、没有 repo sync 缓存，每次全新同步，单次约 11 分钟；
- 有弃用告警：`actions/setup-java@v4`（建议 v5）、checkout/upload-artifact 被强制跑在 Node 24。
- 无 `.gitignore`。

### P6/P7 待真机确认的细节
- `TARGET_SCREEN_DENSITY := 240` + `TW_THEME := portrait_hdpi`：MTK 的面板参数存在 LK 里，我从内核 DTB 里查不到分辨率（`/bus/lcm` 节点无时序属性），无法在沙箱内确认；如果 UI 过大/过小就换 `portrait_mdpi` 或调密度。
- `recovery.fstab` 把 `/persistent` 映射到 `by-name/frp`（生成器沿用原厂 fstab），能挂但语义奇怪，确认是否需要保留。
- `recovery/root/init.recovery.mt6735.rc` 里的 USB `cmode` 写法依赖 MTK 私有节点，建议真机验证 adb/USB 是否正常。

---

## 四、建议的下一步

1. **真机刷入验证**是当前唯一的关键未知项（P1 的 gzip 内核 + 触摸/显示/解密）。
2. 低成本清理（删死脚本、合并重复的 `VENDOR_SECURITY_PATCH`、补注释、加 `.gitignore`、README 说明限制）——**已实施，见第五节**。
3. CI 增强：**push 触发 + ccache + 镜像容量校验已实施**（见第五节）；「固定 revision」仍待定。

---

---

## 五、本次已实施的改动

在上面的审查结论基础上，做了以下修正（均为低风险改动，未触碰构建逻辑）：

| # | 对应问题 | 改动 |
|---|---|---|
| 1 | P3 死代码 | 删除 `extract-files.sh`、`setup-makefiles.sh`（依赖不存在的 `proprietary-files.txt` 与 `tools/extract-utils/`） |
| 2 | P4 重复变量 | `BoardConfig.mk` 中重复且被覆盖的 `VENDOR_SECURITY_PATCH := 2021-08-01` 已删除，并给 2099 防回滚 hack 加了说明注释 |
| 3 | P1 内核格式 | 新增 `tools/compare-kernel.py`（纯标准库）：解析 boot 头、解 gzip、分离 DTB，分别比对 blob/Image/DTB 的 SHA-256，可区分「同内核重打包」与「内核不同」；支持 `--extract` 导出原厂内核。已用合成镜像覆盖 3 种场景（完全一致 / 重打包 / 裸 Image+DTB）+ 异常输入测试 |
| 4 | P1 文档 | `BOARD_KERNEL_IMAGE_NAME` 附近加注说明预编译包是 `Image.gz-dtb`、以及 `TARGET_FORCE_PREBUILT_KERNEL` 无人消费的事实 |
| 5 | P5 CI | workflow 改名为「Build TWRP for m9_x15」；新增 push 触发（`**.md` 变更跳过）、`concurrency` 取消过期构建、`timeout-minutes`、ccache 缓存、构建后校验镜像是否超过 24 MiB、`if-no-files-found: error`；升级 `actions/checkout@v7`、`actions/setup-java@v6`、`actions/upload-artifact@v7` |
| 6 | P5 卫生 | 新增 `.gitignore`（构建产物/镜像 dump/`__pycache__`） |
| 7 | 文档 | 重写 `README.md`（中英双语）：澄清实际产物是「8.1 底包 + TWRP 3.7.0_9」、内核格式与版本、24 MiB 分区余量、无加密解密能力、屏幕密度未验证、防回滚 hack 不可乱改、目录结构 |

**未改动的项**（需要真机或你确认后再动）：
- P1 的最终判定仍取决于用 `tools/compare-kernel.py` 比对原厂镜像的结果；
- P2 的锁定 revision（会牵涉构建可复现策略，且 `twrp-8.1` 清单是否长期维护未知）；
- P6/P7 的屏幕密度、`/persistent→frp` 映射、USB `cmode` 节点。

### 证据来源（可复现的检查方式）
- 本仓库文件 + `git log/stat`
- `gh run list/view`（CI 状态、作业步骤、artifact 大小 21,472,391 B）
- 实际的构建源码：`TeamWin/android_bootable_recovery@android-9.0`（3.7.0_9）、`@android-8.1`、`TeamWin/android_build@android-8.1`、`TeamWin/android_vendor_omni@android-8.1`、`minimal-manifest-twrp/platform_manifest_twrp_omni@twrp-8.1`（`twrp-extras.xml`）、`aosp-mirror/platform_build@android-8.1.0_r51`、`aosp-mirror/platform_system_core@android-8.1.0_r51`
- 用 Python 解析了 `prebuilt/kernel`：gzip 流 6,868,298 B + 尾部 DTB 51,895 B；DTB 的 FDT 结构解析出 `/chosen/bootargs`
