---
name: project-design
description: 项目架构与设计约束
metadata:
  version: "1.0.0"
  lang: "zh-CN"
---

# tb321fu-bt-audio-fix — 设计

## 多语言

**简体中文** | [English](en/DESIGN.md) | [Español](es/DESIGN.md)

## 文档

- 项目概览: [README](../README.md)

- 设计思路: [DESIGN](DESIGN.md)

- 项目状态: [LOG](LOG.md)
- 历史记录: [HISTORY](HISTORY.md)
- 变更日志: [CHANGELOG](CHANGELOG.md)

- 第三方声明: [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)

## 设计目标

- [x] 蓝牙耳机听歌有声音
- [x] 蓝牙通话双方都能听到, 并且使用耳机麦克风
- [x] LE 音频不可用时不在设置里暴露
- [x] 不分发联想的二进制文件, 补丁版 AHAL 在设备上从原厂库生成
- [ ] 让高通 A2DP 硬件 offload 本身能用(LDAC / aptX 走硬件编码)

## 架构

模块在 `post-fs-data` 阶段 bind mount 两个 `/vendor` 文件, 用 `system.prop` 设置蓝牙属性. 不改分区, 重启后失效.

| 目录 | 职责 |
| --- | --- |
| `module/` | 模块本体: `post-fs-data.sh`, `system.prop`, `module.prop`, `files/audio_policy_configuration.xml` |
| `scripts/` | 打包脚本 `pack.sh`; 在电脑上生成音频策略和补丁版 AHAL 的脚本 |
| `out/` | 打包输出, 不提交 |

### 1. 听歌: 关闭 A2DP 硬件 offload

TB321FU 的 vendor 声明支持 A2DP 硬件 offload, 音频策略把 A2DP 口放在 primary 模块下, 由高通 PAL 处理. GSI 里的 AOSP / Google 蓝牙协议栈没有开起 vendor 的 offload 会话, 日志一直是:

```text
btaudio_offload_aidl: update_metadata: ... session ready = 0
PAL: switchDevice: A2DP profile is not ready, ignoring routing request
```

PAL 忽略切到 A2DP 的路由, 声音留在扬声器上. 协议栈为什么没有开起会话没有查清, 见 [LOG](LOG.md#缺陷).

改法是关掉 offload, A2DP 改走 vendor 的 `audio.bluetooth_qti.default.so` 软件编码:

- `system.prop`: `persist.bluetooth.a2dp_offload.disabled=true`, `persist.bluetooth.bluetooth_audio_hal.disabled=false`
- 音频策略 `/vendor/etc/audio/sku_pineapple/audio_policy_configuration.xml`: 删掉 primary 模块下 `BT A2DP Out`, `BT A2DP Headphones`, `BT A2DP Speaker` 三个 devicePort 和到它们的 route; 把只含助听器的 `bluetooth_qti_hearing_aid_audio_policy_configuration.xml` include 换成完整的 `bluetooth_qti_audio_policy_configuration.xml`. `scripts/make_offload_disabled_policy.py` 自动完成这两步.

AOSP 在 offload 关闭时会找 `audio_policy_configuration_a2dp_offload_disabled.xml`, 但 GSI 上它的搜索路径里能否找到这个文件无法确认, 所以模块直接盖住原文件.

### 2. 通话: 去掉 AHAL 的 A2DP 挂起检查

AHAL(`audio.primary.pineapple.so`)打开或切换到 SCO 前, 用 `pal_get_param(PAL_PARAM_ID_BT_A2DP_SUSPENDED)` 确认 A2DP 已挂起, 没挂起就报 `Cannot open stream on SCO if A2dp is not suspended` 并拒绝. 第 1 步之后 A2DP 不在 PAL 里, AHAL 下发 `A2dpSuspended=true` 时 PAL 返回 -22, 挂起状态始终是 0, SCO 打不开或切不过去.

4 处检查结构相同:

```text
mov  w0, #0x10            ; PAL_PARAM_ID_BT_A2DP_SUSPENDED
bl   pal_get_param
cbnz w0, ok
ldrb w8, [x8, #5]         ; a2dp_suspended
cbz  w8, <报错分支>        ; 换成 nop: 1f 20 03 d5
```

ZUI 17.5.10.170 的库(sha256 `f468566521d97efb7309ba89c23104bd22a1853eca744f99cb4d368a40d454af`)中的位置:

| 文件偏移 | 函数 |
| --- | --- |
| `0x547C4` | `StreamOutPrimary::Open` |
| `0x58F24` | `StreamOutPrimary::RouteStream` |
| `0x5EB98` | `StreamInPrimary::Open` |
| `0x613B8` | `StreamInPrimary::RouteStream` |

补丁版 sha256 是 `ecc37b9c8452ccb1aff698697f06e793912d0472cb8946bbcad2ca8d9ed6943d`. `post-fs-data.sh` 每次开机先校验 `/vendor` 上的原厂库, 不匹配就删掉缓存并跳过; 匹配时用 `dd` 写入 4 处 nop, 校验结果的 sha256 后再 bind mount. `scripts/patch_ahal_sco_check.py` 在电脑上做同样的事, 另外核对每处原指令.

### 3. LE 音频: 关闭

LE 音频在这台机器上同样只有 offload 路径, AOSP 协议栈下开不起来(PAL 报 `a2dp handle is not identified`), vendor 的软件路径策略里也没有 BLE 口. `system.prop` 关掉 BAP, CSIP, HAP, VCP, MCP, CCP, TBS 各 profile 和 `ro.bluetooth.leaudio_switcher.supported`, 设置里的 LE 音频开关随之消失. 另外关掉 Pixel 专用, 高通 vendor 不支持的 `persist.bluetooth.opus.enabled`, `bluetooth.core.le_audio.codec_extension_aidl.enabled`, `bluetooth.hfp.swb.supported`.

## 设计约束

- 补丁版 AHAL 只能盖在 sha256 完全匹配的原厂库上; vendor 升级后**禁止**继续使用旧缓存
- 仓库和模块 zip **禁止**包含联想的二进制文件
- 所有修改只用 bind mount 和属性, **禁止**写 `/vendor` 分区
