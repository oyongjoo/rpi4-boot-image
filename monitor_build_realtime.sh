#!/bin/bash

# 실시간 빌드 모니터링 스크립트
CONTAINER_NAME="rpi4-builder-persistent"

echo "🔥 실시간 RPi4 빌드 모니터링 시작"
echo "================================"

# 화면 정리 함수
clear_screen() {
    printf '\033[2J\033[H'
}

# 빌드 상태 표시 함수
show_build_status() {
    clear_screen
    echo "🚀 RPi4 빌드 실시간 모니터링"
    echo "================================"
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 컨테이너 상태 확인
    if ! docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        echo "❌ 컨테이너가 실행되지 않음!"
        exit 1
    fi
    
    # 빌드 프로세스 확인
    BUILD_PROCESSES=$(docker exec $CONTAINER_NAME ps aux | grep make | grep -v grep | wc -l)
    echo "🔧 활성 빌드 프로세스: $BUILD_PROCESSES개"
    
    # 빌드 시간 계산
    BUILD_TIME=$(docker exec $CONTAINER_NAME bash -c 'echo $((($(date +%s) - $(stat -c %Y /rpi-boot/buildroot/output 2>/dev/null || echo $(date +%s)))/60))')
    echo "⏱️  빌드 경과 시간: ${BUILD_TIME}분"
    
    # 빌드된 패키지 수
    PACKAGES=$(docker exec $CONTAINER_NAME find /rpi-boot/buildroot/output/build -maxdepth 1 -type d | wc -l)
    echo "📦 빌드된 패키지: $PACKAGES개"
    
    # 현재 빌드 중인 작업
    echo ""
    echo "🔨 현재 빌드 중인 작업:"
    docker exec $CONTAINER_NAME ps aux | grep make | grep -v grep | head -3 | while read line; do
        echo "   $line" | cut -c1-80
    done
    
    # 최근 로그 (마지막 5줄)
    echo ""
    echo "📝 최근 빌드 로그:"
    echo "---"
    # Buildroot 로그 확인 시도
    if docker exec $CONTAINER_NAME test -f /rpi-boot/buildroot/output/build/build-time.log; then
        docker exec $CONTAINER_NAME tail -3 /rpi-boot/buildroot/output/build/build-time.log 2>/dev/null || echo "   빌드 로그 읽기 중..."
    else
        echo "   빌드 로그 생성 중..."
    fi
    
    echo "---"
    echo ""
    echo "💡 실시간 상세 로그를 보려면: Ctrl+C 후 'docker logs -f $CONTAINER_NAME'"
    echo "🔄 자동 새로고침 중... (Ctrl+C로 종료)"
}

# 메인 루프
while true; do
    show_build_status
    sleep 5
done