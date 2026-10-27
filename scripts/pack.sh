#!/usr/bin/env bash
# 打 KernelSU / Magisk 模块 zip. 用法: scripts/pack.sh [输出 zip]
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
VER=$(sed -n 's/^version=//p' "$ROOT/module/module.prop")
ZIP=$(realpath -m "${1:-$ROOT/out/tb321fu_bt_audio_fix_$VER.zip}")
if grep -l $'\r' "$ROOT"/module/*.sh "$ROOT"/module/*.prop; then echo "CRLF in module files" >&2; exit 1; fi
mkdir -p "$(dirname "$ZIP")"; rm -f "$ZIP"
(cd "$ROOT/module" && zip -q -X -r "$ZIP" module.prop system.prop post-fs-data.sh files/audio_policy_configuration.xml)
unzip -l "$ZIP"
sha256sum "$ZIP"
