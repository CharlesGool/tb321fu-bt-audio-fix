#!/usr/bin/env python3
"""给原厂 audio.primary.pineapple.so 去掉 "SCO 前必须先挂起 A2DP" 的检查.

背景: A2DP 改走 bluetooth_qti 软件编码后, PAL 里的 A2DP 设备从来不会"连上",
AHAL 下发 A2dpSuspended=true 时 PAL 返回 -22, 但 pal_get_param(PAL_PARAM_ID_BT_A2DP_SUSPENDED)
仍然成功并返回 a2dp_suspended=0. AHAL 在下面 4 处看到"未挂起"就拒绝打开/切换到 SCO,
表现是蓝牙通话一开始双方都听不见, 或者麦克风回落到平板内置麦克风.

4 处都是同一结构:
    mov  w0, #0x10            ; PAL_PARAM_ID_BT_A2DP_SUSPENDED
    bl   pal_get_param
    cbnz w0, ok ; ... ldrb w8, [x8, #5]   ; a2dp_suspended
    cbz  w8, <ERR "... if A2dp is not suspended">
把最后这条 cbz 换成 nop, 其余逻辑不变.

只适用于 ZUI 17.5.10.170 (TB321FU) 的 vendor, 输入不匹配就拒绝.
"""
import hashlib
import struct
import sys

STOCK_SHA256 = "f468566521d97efb7309ba89c23104bd22a1853eca744f99cb4d368a40d454af"
NOP = struct.pack("<I", 0xD503201F)

# (偏移, 原指令, 说明); .text 的虚拟地址和文件偏移一致
PATCHES = [
    (0x547C4, "StreamOutPrimary::Open      cbz w8, 0x54af4"),
    (0x58F24, "StreamOutPrimary::RouteStream cbz w8, 0x59120"),
    (0x5EB98, "StreamInPrimary::Open       cbz w8, 0x5ec64"),
    (0x613B8, "StreamInPrimary::RouteStream  cbz w8, 0x61788"),
]


def cbz_w8(at, target):
    """编码 cbz w8, target (32 位寄存器版本)."""
    imm19 = ((target - at) >> 2) & 0x7FFFF
    return struct.pack("<I", 0x34000000 | (imm19 << 5) | 8)


TARGETS = {0x547C4: 0x54AF4, 0x58F24: 0x59120, 0x5EB98: 0x5EC64, 0x613B8: 0x61788}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    data = bytearray(open(src, "rb").read())
    sha = hashlib.sha256(data).hexdigest()
    if sha != STOCK_SHA256:
        sys.exit(f"input sha256 {sha} != stock {STOCK_SHA256}, refusing to patch")
    for off, desc in PATCHES:
        expect = cbz_w8(off, TARGETS[off])
        if data[off:off + 4] != expect:
            sys.exit(f"unexpected bytes at {off:#x} ({desc}): {data[off:off + 4].hex()}")
        data[off:off + 4] = NOP
        print(f"patched {off:#x}  {desc} -> nop")
    open(dst, "wb").write(data)
    print(f"wrote {dst} sha256 {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
