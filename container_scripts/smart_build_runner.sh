#!/bin/bash
set -e

# 작업 공간 설정
WORKSPACE="/workspace"
LOGS="/logs"
STAGE_FILE="$WORKSPACE/current_stage.txt"

# 함수들
log_info() {
    echo "[$(date '+%H:%M:%S')] INFO: $1" | tee -a $LOGS/container.log
}

log_error() {
    echo "[$(date '+%H:%M:%S')] ERROR: $1" | tee -a $LOGS/container.log
}

update_stage() {
    echo "$1:$(date -Iseconds)" > $STAGE_FILE
    log_info "단계 변경: $1"
}

# 재시작 지점 확인
RESUME_STAGE=""
if [ -f "$STAGE_FILE" ]; then
    RESUME_STAGE=$(cut -d: -f1 $STAGE_FILE)
    log_info "이전 단계에서 재시작: $RESUME_STAGE"
fi

# 각 빌드 단계 실행
case "$RESUME_STAGE" in
    ""|"docker_build"|"kernel_config")
        update_stage "kernel_config"
        /container_scripts/kernel_config.sh || exit 1
        ;&
    "kernel_compile")
        update_stage "kernel_compile" 
        /container_scripts/kernel_compile.sh || exit 1
        ;&
    "buildroot_config")
        update_stage "buildroot_config"
        /container_scripts/buildroot_config.sh || exit 1
        ;&
    "buildroot_build")
        update_stage "buildroot_build"
        /container_scripts/buildroot_build.sh || exit 1
        ;&
    "image_create")
        update_stage "image_create"
        /container_scripts/image_create.sh || exit 1
        ;&
    *)
        update_stage "complete"
        log_info "모든 빌드 단계 완료!"
        ;;
esac
