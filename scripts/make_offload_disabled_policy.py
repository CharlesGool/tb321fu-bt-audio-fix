#!/usr/bin/env python3
"""从原厂 sku_pineapple 音频策略生成 A2DP 关闭 offload 时用的策略文件.

AOSP 在 ro.bluetooth.a2dp_offload.supported=true, persist.bluetooth.a2dp_offload.disabled=true,
persist.bluetooth.bluetooth_audio_hal.disabled=false 时找 audio_policy_configuration_a2dp_offload_disabled.xml
(两个 disabled 都是 true 时才找 _bluetooth_legacy_hal.xml). 搜索路径里有没有 /system/etc 没法确认,
所以测试模块直接 bind mount 盖住 /vendor/etc/audio/sku_pineapple/audio_policy_configuration.xml.

改动:
1. primary 模块里删掉 BT A2DP Out/Headphones/Speaker 三个设备口和它们的路由
   (这些口走高通 offload).
2. 只含助听器的 bluetooth_qti include 换成完整的 bluetooth_qti 模块
   (A2DP + 助听器, 由 vendor 的 audio.bluetooth_qti.default.so 做软件编码).
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

A2DP_OUT = r'BT A2DP (?:Out|Headphones|Speaker)'

text, n_ports = re.subn(
    r'[ \t]*<devicePort tagName="' + A2DP_OUT + r'"[^>]*>.*?</devicePort>\n', '', text, flags=re.S)
text, n_routes = re.subn(
    r'[ \t]*<route type="mix" sink="' + A2DP_OUT + r'"[^>]*/>\n', '', text, flags=re.S)
text, n_inc = re.subn(
    r'/vendor/etc/bluetooth_qti_hearing_aid_audio_policy_configuration\.xml',
    '/vendor/etc/bluetooth_qti_audio_policy_configuration.xml', text)

if (n_ports, n_routes, n_inc) != (3, 3, 1):
    sys.exit(f"unexpected source layout: ports={n_ports} routes={n_routes} include={n_inc}")
if 'BT A2DP Out' in text.split('<!-- A2DP Audio HAL -->')[0]:
    sys.exit("BT A2DP Out still referenced in primary module")

open(dst, "w", encoding="utf-8").write(text)
print(f"wrote {dst}")
