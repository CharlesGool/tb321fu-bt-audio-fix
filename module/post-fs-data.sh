#!/system/bin/sh
# 开机时 bind mount 两个 /vendor 文件, 重启即失效, 卸载模块不用清理.
# 1. 音频策略: primary 里去掉走高通 offload 的 A2DP 口, A2DP 交给 bluetooth_qti 软件编码
# 2. audio.primary: 在设备上从原厂库生成补丁版(4 处 cbz -> nop), 只认 ZUI 17.5.10.170 的原厂库
MODDIR=${0%/*}
LOG=$MODDIR/mount.log

POL_SRC=$MODDIR/files/audio_policy_configuration.xml
POL_DST=/vendor/etc/audio/sku_pineapple/audio_policy_configuration.xml
AHAL_DST=/vendor/lib64/hw/audio.primary.pineapple.so
AHAL_OUT=$MODDIR/files/audio.primary.pineapple.so
STOCK_SHA256=f468566521d97efb7309ba89c23104bd22a1853eca744f99cb4d368a40d454af
PATCHED_SHA256=ecc37b9c8452ccb1aff698697f06e793912d0472cb8946bbcad2ca8d9ed6943d
# 和 scripts/patch_ahal_sco_check.py 的 PATCHES 一致(0x547C4 0x58F24 0x5EB98 0x613B8)
OFFSETS="346052 364324 387992 398264"

bind() {
    if [ ! -f "$2" ]; then
        echo "skip $2: target missing" >> $LOG
        return
    fi
    chcon "$3" "$1"
    chmod 0644 "$1"
    mount -o bind "$1" "$2" && echo "ok $2" >> $LOG || echo "FAIL $2" >> $LOG
}

sha() { sha256sum "$1" 2>/dev/null | cut -d' ' -f1; }

echo "== $(date)" > $LOG
bind $POL_SRC $POL_DST u:object_r:vendor_configs_file:s0

if [ "$(sha $AHAL_DST)" != "$STOCK_SHA256" ]; then
    echo "skip AHAL: $AHAL_DST sha256 $(sha $AHAL_DST) is not ZUI 17.5.10.170 stock" >> $LOG
    rm -f $AHAL_OUT
else
    if [ "$(sha $AHAL_OUT)" != "$PATCHED_SHA256" ]; then
        rm -f $AHAL_OUT
        cp $AHAL_DST $AHAL_OUT.tmp
        for off in $OFFSETS; do
            printf '\037\040\003\325' | dd of=$AHAL_OUT.tmp bs=1 seek=$off count=4 conv=notrunc 2>/dev/null
        done
        if [ "$(sha $AHAL_OUT.tmp)" = "$PATCHED_SHA256" ]; then
            mv $AHAL_OUT.tmp $AHAL_OUT
            echo "patched $AHAL_DST" >> $LOG
        else
            echo "patch result sha256 mismatch, not using it" >> $LOG
            rm -f $AHAL_OUT.tmp
        fi
    fi
    [ -f $AHAL_OUT ] && bind $AHAL_OUT $AHAL_DST u:object_r:vendor_file:s0
fi

ls -lZ $POL_DST $AHAL_DST >> $LOG 2>&1
