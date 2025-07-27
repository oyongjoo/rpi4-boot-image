#!/bin/bash
set -e
cd /rpi-boot/buildroot

echo "Buildroot 설정 시작..."
# 사용자 테이블 생성
echo "pi -1 pi -1 =raspberry /home/pi /bin/bash sudo" > board/users_table.txt

# 기본 설정
make raspberrypi4_64_defconfig
# ... (기존 설정들)

echo "Buildroot 설정 완료"
