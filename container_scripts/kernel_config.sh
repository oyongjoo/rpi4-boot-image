#!/bin/bash
set -e
cd /rpi-boot/linux

echo "커널 설정 시작..."
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- bcm2711_defconfig

# 추가 설정들
echo '# Disable Broadcom WiFi/BT' >> .config
echo '# CONFIG_BRCMFMAC is not set' >> .config
echo '# CONFIG_BRCMUTIL is not set' >> .config
# ... (기존 설정들)

echo "커널 설정 완료"
