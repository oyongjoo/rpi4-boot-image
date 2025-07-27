#!/bin/bash
set -e
cd /rpi-boot/buildroot

echo "Buildroot 빌드 시작..."
echo "예상 소요 시간: 10-20분"

# post-build 스크립트 생성
echo "#!/bin/bash" > board/post-build.sh
# ... (기존 post-build 내용)
chmod +x board/post-build.sh

# 빌드 실행
make -j1 2>&1 | while IFS= read -r line; do
    echo "$line"
    echo "$(date -Iseconds): $line" >> /workspace/buildroot_progress.log
    if [[ "$line" == *"error:"* ]] || [[ "$line" == *"Error"* ]]; then
        echo "BUILDROOT_ERROR: $line" >> /logs/errors.log
    fi
done

echo "Buildroot 빌드 완료"
