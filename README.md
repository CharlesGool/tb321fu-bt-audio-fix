# tb321fu-bt-audio-fix

**简体中文** | [English](doc/en/README.md) | [Español](doc/es/README.md)

修复拯救者 Y700 三代 (TB321FU) 刷 Pixel / AOSP 类 GSI 后蓝牙耳机没声音, 蓝牙通话没声音的问题, 做成 KernelSU / Magisk 模块.

[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

## 文档

- 项目概览: [README](README.md)

- 设计思路: [DESIGN](doc/DESIGN.md)

- 项目状态: [LOG](doc/LOG.md)
- 历史记录: [HISTORY](doc/HISTORY.md)
- 变更日志: [CHANGELOG](doc/CHANGELOG.md)

- 第三方声明: [THIRD_PARTY_NOTICES](doc/THIRD_PARTY_NOTICES.md)

## 简介

| 问题 | 修复 | 适用范围 |
| --- | --- | --- |
| 部分蓝牙耳机没声音, 或声音从平板扬声器出来 | A2DP 不走高通硬件 offload, 改走 vendor 自带的软件编码 | TB321FU 原厂 vendor |
| 戴蓝牙耳机通话, 一开始双方都听不到, 或麦克风用的是平板的 | 去掉 AHAL 里 4 处 "A2DP 必须已挂起" 的检查 | **只适用于 ZUI 17.5.10.170** 的 vendor, 其他版本自动跳过 |
| 打开 LE 音频后没声音 | 关掉 LE 音频, 双模耳机走经典蓝牙 | TB321FU 原厂 vendor |

每个问题的原因和具体改法见 [DESIGN](doc/DESIGN.md#架构). 已知问题见 [LOG](doc/LOG.md#缺陷).

[TB321FU_PixelOS_15_Tangorpro](https://github.com/CharlesGool/TB321FU_PixelOS_15_Tangorpro) 已经内置这些修复, 用这个 ROM 不需要装本模块.

## 要求

- 拯救者 Y700 三代 (TB321FU), vendor 是原厂 ZUI; 蓝牙通话修复要求 ZUI 17.5.10.170
- system 分区刷了 Pixel / AOSP 类 GSI
- KernelSU 或 Magisk

## 安装

### 快速安装

```bash
scripts/pack.sh
adb push out/tb321fu_bt_audio_fix_v1.zip /sdcard/Download/
```

在 KernelSU 或 Magisk 里安装 `/sdcard/Download/tb321fu_bt_audio_fix_v1.zip`, 重启.

### 常规安装

同快速安装. 打包只需要 `zip`, 不需要原厂文件.

装过旧的 `tb321fu_gsi_fix` 测试模块(v1 到 v4)的, 先卸载它, 两个模块会重复挂载同样的文件.

## 指南

### 检查是否生效

开机后看 `/data/adb/modules/tb321fu_bt_audio_fix/mount.log`:

```text
ok /vendor/etc/audio/sku_pineapple/audio_policy_configuration.xml
patched /vendor/lib64/hw/audio.primary.pineapple.so
ok /vendor/lib64/hw/audio.primary.pineapple.so
```

`patched` 只在第一次开机出现, 之后用缓存的补丁版. 出现 `skip AHAL: ... is not ZUI 17.5.10.170 stock` 时, vendor 版本不对, 通话修复没有生效, 听歌修复照常生效.

### 在别的 vendor 版本上重做通话修复

1. 拉原厂库:

   ```bash
   adb pull /vendor/lib64/hw/audio.primary.pineapple.so
   ```

2. 找报错字符串:

   ```bash
   strings -t x audio.primary.pineapple.so | grep "A2dp is not suspended"
   ```

   ZUI 17.5.10.170 上有 3 条: `Cannot open stream on SCO ...`, `Cannot route stream to SCO ...`, `Cannot route stream from SCO ...`.
3. 反汇编(`aarch64-linux-gnu-objdump -d`, Ghidra 或 IDA), 找引用这些字符串的代码. 每处往上找最近一条 `cbz w8, <报错分支>`, 它前面应有 `mov w0, #0x10`, `bl pal_get_param` 和 `ldrb w8, [x8, #5]`. 这条 `cbz` 的文件偏移就是补丁位置. 用 `readelf -l` 确认 `.text` 的虚拟地址和文件偏移的关系(17.5.10.170 上两者相同).
4. 改 `scripts/patch_ahal_sco_check.py` 的 `STOCK_SHA256`, `PATCHES`, `TARGETS`, 运行它得到补丁版的 sha256:

   ```bash
   python3 scripts/patch_ahal_sco_check.py audio.primary.pineapple.so patched.so
   ```

5. 改 `module/post-fs-data.sh` 的 `STOCK_SHA256`, `PATCHED_SHA256` 和 `OFFSETS`(十进制), 重新打包.

找到的位置不是 4 处, 或者代码结构和上面不同时, 说明这版 AHAL 的逻辑变了, 这个改法不适用.

### 音频策略换了版本

`scripts/make_offload_disabled_policy.py` 从原厂策略生成 `module/files/audio_policy_configuration.xml`, 原文件结构对不上时报错退出:

```bash
adb pull /vendor/etc/audio/sku_pineapple/audio_policy_configuration.xml stock.xml
python3 scripts/make_offload_disabled_policy.py stock.xml module/files/audio_policy_configuration.xml
```

## 升级

从旧的 `tb321fu_gsi_fix` 测试模块迁移: 在 KernelSU 或 Magisk 里卸载 `tb321fu_gsi_fix`, 重启, 再安装本模块. 旧模块里的亮度 overlay 不在本模块中, 需要的话用 TB321FU_PixelOS_15_Tangorpro 的 ROM.

## 卸载

### 快速卸载

在 KernelSU 或 Magisk 里卸载模块, 重启. 所有修改都是开机时的 bind mount, 不改 `/vendor` 分区, 重启后恢复原样.

### 完全卸载

同快速卸载. 模块目录(含缓存的补丁版库和日志)由 KernelSU 或 Magisk 一并删除.

## 致谢

暂无

## 许可证

MIT License(`MIT`), 全文见 [LICENSE](LICENSE). `module/files/audio_policy_configuration.xml` 由联想原厂配置文件修改而来, 见 [THIRD_PARTY_NOTICES](doc/THIRD_PARTY_NOTICES.md).
