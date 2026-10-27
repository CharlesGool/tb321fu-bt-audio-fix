---
name: project-log
description: 项目缺陷, 限制, 决策和交接
metadata:
  version: "1.0.0"
  lang: "zh-CN"
---

# 日志

## 多语言

**简体中文** | [English](en/LOG.md) | [Español](es/LOG.md)

## 文档

- 项目概览: [README](../README.md)

- 设计思路: [DESIGN](DESIGN.md)

- 项目状态: [LOG](LOG.md)
- 历史记录: [HISTORY](HISTORY.md)
- 变更日志: [CHANGELOG](CHANGELOG.md)

- 第三方声明: [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)

## 记录

- [历史记录](HISTORY.md)
- [变更日志](CHANGELOG.md)

## 缺陷

- [ ] 本模块的设备端打补丁方式没有上机验证. 同样的修复以旧测试模块 `tb321fu_gsi_fix` v4 和 TB321FU_PixelOS_15_Tangorpro V1 到 V6 的形式在平板上验证过(Galaxy Buds3 Pro AAC 听歌, Telegram 蓝牙通话)
- [ ] 微信语音通话不请求蓝牙 SCO, 使用平板麦克风; 这是微信自己的行为
- [ ] SBC 编码没有单独测试

## 限制

- 修复绕开了 A2DP 硬件 offload, 没有修好它: LDAC / aptX 由 CPU 软件编码. 协议栈为什么没有开起 vendor 的 offload 会话没有查清; vendor 的 provider 是 `android.hardware.bluetooth.audio` AIDL V3, 怀疑和 Google 蓝牙 apex 的 offload 协商路径不匹配(未证实)
- LE 音频只有 offload 路径, 软件路径下不可用
- 通话修复依赖具体 AHAL 二进制的偏移, 每个 vendor 版本都要重新找

## 决策

| 日期 | 决策 | 状态 | 原因 |
| --- | --- | --- | --- |
| 2026-10-27 | 补丁版 AHAL 在设备上生成, 不放进仓库和 zip | 接受 | 不分发联想的二进制文件 |
| 2026-10-27 | 盖住原厂音频策略, 不提供 `_a2dp_offload_disabled.xml` | 接受 | GSI 上无法确认 AOSP 能找到该文件 |
| 2026-10-26 | 不走 KLCOS 的 sysbta 路线 | 拒绝 | 要换掉整个 Google 蓝牙 apex, 本质上也是软件编码 |

## 交接

- 分支: `main`
- 已完成: 从 TB321FU_PixelOS_15_Tangorpro 的 `bt-audio/` 和 `ksu-module/` 拆出蓝牙部分; `post-fs-data.sh` 改为在设备上打补丁; 文档
- 检查: 在电脑上用 dash 和 busybox 模拟设备端 `dd` 补丁, 结果 sha256 与 `scripts/patch_ahal_sco_check.py` 一致(`ecc37b9c...`); `sh -n` 语法检查通过; `scripts/pack.sh` 打包成功
- 剩余: 上机安装验证; 验证通过后发布 v1 Release
- 临时项目规则: 未发现
