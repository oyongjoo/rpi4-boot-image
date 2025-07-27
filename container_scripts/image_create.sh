#!/bin/bash
set -e

echo "최종 이미지 생성 시작..."

# 기존 create_rpi4_image.sh 내용을 여기에 포함
cd /rpi-boot
./create_rpi4_image.sh

echo "최종 이미지 생성 완료"
