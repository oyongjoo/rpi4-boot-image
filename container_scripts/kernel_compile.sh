#!/bin/bash
set -e
cd /rpi-boot/linux

echo "커널 컴파일 시작..."
echo "예상 소요 시간: 20-40분"

# 진행률 모니터링과 함께 컴파일
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j1 Image modules dtbs 2>&1 | \
    while IFS= read -r line; do
        echo "$line"
        # 진행률 정보를 workspace에 저장
        if [[ "$line" == *"CC"* ]] || [[ "$line" == *"LD"* ]]; then
            echo "$(date -Iseconds): $line" >> /workspace/compile_progress.log
        fi
        # 오류 패턴 체크
        if [[ "$line" == *"error:"* ]] || [[ "$line" == *"Error"* ]]; then
            echo "COMPILE_ERROR: $line" >> /logs/errors.log
        fi
    done

echo "커널 컴파일 완료"
