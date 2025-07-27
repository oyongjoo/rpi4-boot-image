# RPi4 빌드 문제 해결 가이드

## 📋 목차
1. [일반적인 빌드 오류](#일반적인-빌드-오류)
2. [Docker 관련 문제](#docker-관련-문제)
3. [컨테이너 관리 문제](#컨테이너-관리-문제)
4. [빌드 모니터링 도구](#빌드-모니터링-도구)
5. [시스템 리소스 문제](#시스템-리소스-문제)
6. [권한 관련 문제](#권한-관련-문제)

---

## 일반적인 빌드 오류

### ❌ "You must install '/usr/bin/file' on your build machine"

**증상:**
```
You must install '/usr/bin/file' on your build machine
make: *** [support/dependencies/dependencies.mk:27: dependencies] Error 1
```

**원인:** `util-linux` 패키지의 `file` 유틸리티 누락

**해결방법:**
```bash
# 1. 즉시 해결 (현재 빌드용)
docker exec rpi4-builder-persistent apt-get update
docker exec rpi4-builder-persistent apt-get install -y file

# 2. 영구 해결 (Dockerfile 수정)
# Dockerfile에 다음 추가:
RUN apt-get update && apt-get install -y \
    util-linux \
    && rm -rf /var/lib/apt/lists/*
```

**예방:** Dockerfile에 `util-linux` 패키지 포함

### ❌ 커널 컴파일 실패 - 메모리 부족

**증상:**
```
gcc: fatal error: Killed signal terminated program cc1
make[2]: *** [scripts/Makefile.build:250: kernel/fork.o] Error 1
```

**원인:** 컴파일 과정에서 메모리 부족

**해결방법:**
```bash
# 1. 병렬 빌드 수 감소
make -j4  # 대신 make -j8

# 2. 스왑 메모리 확인
docker exec rpi4-builder-persistent free -h
docker exec rpi4-builder-persistent swapon -s

# 3. Docker 메모리 할당 증가
# Docker Desktop 설정에서 메모리 8GB → 12GB+ 증가
```

### ❌ 네트워크 다운로드 실패

**증상:**
```
--2025-07-26 14:35:40--  http://example.com/package.tar.gz
Resolving example.com... failed: Name or service not known.
```

**원인:** 네트워크 연결 문제 또는 DNS 설정 오류

**해결방법:**
```bash
# 1. 네트워크 연결 확인
ping google.com

# 2. Docker 네트워크 재시작
sudo systemctl restart docker

# 3. DNS 설정 확인
docker exec rpi4-builder-persistent cat /etc/resolv.conf

# 4. 프록시 환경인 경우
docker run --env http_proxy=http://proxy:port ...
```

---

## Docker 관련 문제

### ❌ "Cannot connect to the Docker daemon"

**증상:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. 
Is the docker daemon running?
```

**해결방법:**
```bash
# 1. Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 2. 사용자 권한 확인
sudo usermod -aG docker $USER
# 로그아웃 후 재로그인 필요

# 3. WSL2 환경에서
# Docker Desktop이 실행 중인지 확인
```

### ❌ "No space left on device"

**증상:**
```
No space left on device
write error: No space left on device
```

**해결방법:**
```bash
# 1. 디스크 사용량 확인
df -h
docker system df

# 2. Docker 정리
docker system prune -a -f
docker volume prune -f

# 3. 컨테이너 로그 정리
docker logs rpi4-builder-persistent --tail 100

# 4. 임시 파일 정리
sudo apt-get clean
sudo apt-get autoremove
```

---

## 컨테이너 관리 문제

### ❌ 컨테이너가 계속 종료됨

**증상:** 빌드 중 오류 발생 시 컨테이너가 자동으로 삭제되어 진행상황 손실

**원인:** `--rm` 플래그 사용으로 자동 삭제 설정

**해결방법:**
```python
# build.py 개선 버전 사용
def start_or_create_container(self):
    if self.check_container_exists():
        if not self.check_container_running():
            self.run_command(f"docker start {self.container_name}")
    else:
        # --rm 제거, 지속적 컨테이너
        create_cmd = f"""docker run -d --name {self.container_name} \
            --privileged \
            -v $(pwd):/output \
            {self.image_name} \
            sleep infinity"""
```

### ❌ "Container name already in use"

**증상:**
```
docker: Error response from daemon: Conflict. The container name "rpi4-builder-persistent" is already in use
```

**해결방법:**
```bash
# 1. 기존 컨테이너 확인
docker ps -a --filter name=rpi4-builder-persistent

# 2. 컨테이너 재시작 (권장)
docker start rpi4-builder-persistent

# 3. 강제 삭제 후 재생성 (주의: 진행상황 손실)
docker rm -f rpi4-builder-persistent
```

---

## 빌드 모니터링 도구

### 📊 실시간 상태 확인
```bash
# 빌드 진행 여부 확인
docker exec rpi4-builder-persistent ps aux | grep make

# 시스템 리소스 모니터링
docker exec rpi4-builder-persistent bash -c "
echo '=== 시스템 상태 ==='
echo 'CPU:' \$(nproc) '코어'
echo 'Memory:' \$(free -h | grep Mem | awk '{print \$3\"/\"\$2}')
echo 'Disk:' \$(df -h /rpi-boot | tail -1 | awk '{print \$5\" 사용\"}')
echo 'Build processes:' \$(ps aux | grep make | grep -v grep | wc -l)
"
```

### 📈 빌드 진행률 확인
```bash
# 빌드된 패키지 수
docker exec rpi4-builder-persistent bash -c "
echo 'Built packages:' \$(find /rpi-boot/buildroot/output/build -maxdepth 1 -type d | wc -l)
"

# 최종 이미지 생성 여부
docker exec rpi4-builder-persistent bash -c "
if [ -f /rpi-boot/buildroot/output/images/sdcard.img ]; then
    echo '✅ Build completed'
    ls -lh /rpi-boot/buildroot/output/images/sdcard.img
else
    echo '⏳ Build in progress'
fi
"
```

### 📝 로그 분석
```bash
# 빌드 타임라인 확인
docker exec rpi4-builder-persistent tail -20 /rpi-boot/buildroot/output/build/build-time.log

# 에러 로그 검색
docker exec rpi4-builder-persistent find /rpi-boot/buildroot/output/build -name "*.log" -exec grep -l "error\|Error\|ERROR" {} \;

# 실시간 로그 스트리밍
docker logs -f rpi4-builder-persistent
```

---

## 시스템 리소스 문제

### ⚠️ 메모리 사용량 최적화

**모니터링:**
```bash
# 메모리 사용량 실시간 확인
watch -n 5 'docker exec rpi4-builder-persistent free -h'

# 프로세스별 메모리 사용량
docker exec rpi4-builder-persistent ps aux --sort=-%mem | head -10
```

**최적화:**
```bash
# 1. 병렬 빌드 수 조정
make -j4  # 메모리 부족 시 코어 수 감소

# 2. 스왑 활성화 확인
docker exec rpi4-builder-persistent swapon -s

# 3. 캐시 정리
docker exec rpi4-builder-persistent bash -c "
sync
echo 3 > /proc/sys/vm/drop_caches
"
```

### 💾 디스크 공간 관리

**확인:**
```bash
# 전체 디스크 사용량
df -h

# Docker 데이터 사용량
docker system df

# 컨테이너별 크기
docker exec rpi4-builder-persistent du -sh /rpi-boot/*
```

**정리:**
```bash
# 빌드 캐시 정리
docker exec rpi4-builder-persistent bash -c "
cd /rpi-boot/linux && make clean
cd /rpi-boot/buildroot && make clean
"

# 임시 파일 정리
docker exec rpi4-builder-persistent find /tmp -type f -atime +1 -delete
```

---

## 권한 관련 문제

### ❌ "Permission denied"

**증상:**
```
/bin/bash: ./build_script.sh: Permission denied
```

**해결방법:**
```bash
# 1. 스크립트 실행 권한 부여
chmod +x build.py
chmod +x monitor_build_realtime.sh

# 2. Docker 권한 확인
sudo usermod -aG docker $USER
# 재로그인 필요

# 3. 컨테이너 내부 권한
docker exec rpi4-builder-persistent chmod -R 755 /rpi-boot
```

### ❌ WSL2 환경 특수 문제

**파일 권한 불일치:**
```bash
# WSL2에서 Windows 파일시스템 접근 시
# /mnt/c/ 경로 대신 WSL 내부 경로 사용 권장
cd /home/liam/docker/rpi4-boot-image  # ✅ 권장
cd /mnt/c/Users/liam/docker/...       # ❌ 비권장
```

**Docker 서비스 문제:**
```bash
# WSL2에서 Docker Desktop 연동 확인
docker context list
docker version
```

---

## 진단 스크립트

### 🔍 통합 진단 도구
```bash
#!/bin/bash
# diagnose_build.sh

echo "=== RPi4 빌드 환경 진단 ==="

echo "1. 시스템 정보:"
echo "   OS: $(uname -a)"
echo "   Docker: $(docker --version)"
echo "   Available memory: $(free -h | grep Mem | awk '{print $2}')"
echo "   Available disk: $(df -h . | tail -1 | awk '{print $4}')"

echo ""
echo "2. Docker 상태:"
echo "   Service: $(systemctl is-active docker 2>/dev/null || echo 'N/A')"
echo "   Containers: $(docker ps --filter name=rpi4-builder-persistent --format 'table {{.Status}}')"

echo ""
echo "3. 빌드 환경:"
if docker exec rpi4-builder-persistent test -d /rpi-boot 2>/dev/null; then
    echo "   ✅ Build environment ready"
    echo "   Build processes: $(docker exec rpi4-builder-persistent ps aux | grep make | grep -v grep | wc -l)"
else
    echo "   ❌ Build environment not ready"
fi

echo ""
echo "4. 리소스 사용량:"
if docker ps --filter name=rpi4-builder-persistent | grep -q rpi4-builder-persistent; then
    echo "   Memory: $(docker exec rpi4-builder-persistent free -h | grep Mem | awk '{print $3"/"$2}')"
    echo "   Disk: $(docker exec rpi4-builder-persistent df -h /rpi-boot 2>/dev/null | tail -1 | awk '{print $5" used"}' || echo 'N/A')"
else
    echo "   ❌ Container not running"
fi
```

---

## 🆘 긴급 복구 가이드

### 빌드 완전 실패 시
```bash
# 1. 모든 정리 후 재시작
docker rm -f rpi4-builder-persistent
docker system prune -f
./build.py

# 2. 수동 디버깅
docker run -it --rm --privileged -v $(pwd):/output rpi4-boot-builder bash
# 컨테이너 내부에서 수동 빌드 단계별 실행
```

### 시스템 리소스 부족 시
```bash
# 1. 즉시 메모리 확보
sudo sync
sudo echo 3 > /proc/sys/vm/drop_caches

# 2. 디스크 공간 확보
docker system prune -a -f
sudo apt-get autoremove
sudo apt-get clean

# 3. 스왑 활성화
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

**마지막 업데이트**: 2025-07-27  
**적용 환경**: WSL2, Docker, Ubuntu 22.04  
**테스트 상태**: ✅ 실전 검증 완료