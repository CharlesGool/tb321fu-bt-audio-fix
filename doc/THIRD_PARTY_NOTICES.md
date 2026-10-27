---
name: project-third-party-notices
description: 第三方署名与合规声明
metadata:
  version: "1.0.0"
  lang: "zh-CN"
---

# 第三方声明

## 多语言

**简体中文** | [English](en/THIRD_PARTY_NOTICES.md) | [Español](es/THIRD_PARTY_NOTICES.md)

## 文档

- 项目概览: [README](../README.md)

- 设计思路: [DESIGN](DESIGN.md)

- 项目状态: [LOG](LOG.md)
- 历史记录: [HISTORY](HISTORY.md)
- 变更日志: [CHANGELOG](CHANGELOG.md)

- 第三方声明: [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)

## 第三方声明

### 组件清单

| 组件名称 | 版本或哈希 | 上游地址 | 许可证类型 | 使用方式 | 版权归属 | 发布合规义务 | 核验日期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TB321FU 原厂音频策略 `sku_pineapple/audio_policy_configuration.xml` | ZUI 17.5.10.170 | 联想 TB321FU 原厂 vendor 分区 | 未知(未附许可证) | 修改后作为 `module/files/audio_policy_configuration.xml` 分发 | Lenovo / Qualcomm | 未确定 | 2026-10-27 |

### 许可证文本

原文件没有附带许可证.

### 源代码提供

不分发二进制文件. 补丁版 `audio.primary.pineapple.so` 只在用户设备上从其自己的原厂文件生成.

### 合规审查

音频策略是配置文件, 改动是删除 3 个设备口及其路由, 替换 1 个 include. 原文件能否再分发无法确定.
