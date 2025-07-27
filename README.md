# 라즈베리파이 4 커널 빌드 시스템

완전한 부팅 가능한 라즈베리파이 4 이미지를 Docker 환경에서 빌드하는 자동화 시스템입니다.

## 🚀 빠른 시작

### 기본 빌드
```bash
# Python 스크립트로 빌드 (권장 - 기존 컨테이너 재사용)
python3 build.py

# 또는 Docker Compose로 새로운 빌드 환경
docker-compose up -d builder
docker exec rpi4-compose-builder /rpi-boot/build_all.sh
```

### 모니터링과 함께 빌드
```bash
# 실시간 모니터링
./monitor_build_realtime.sh

# 또는 별도 터미널에서
docker-compose --profile monitor up
```

## 📁 주요 파일

- `build.py` - 메인 빌드 스크립트 (컨테이너 유지형, 오류 자동 복구)
- `monitor_build_realtime.sh` - 실시간 빌드 모니터링
- `Dockerfile` - Docker 빌드 환경 설정
- `docker-compose.yml` - 멀티 서비스 Docker 설정

## 🛠️ 사용법

### 1. Python 빌드 스크립트 (권장)
```bash
python3 build.py        # 기본 빌드
./build.py             # 실행 권한이 있는 경우
```

### 2. Docker Compose
```bash
# 새로운 빌드 환경 (기존 build.py와 별도)
docker-compose up -d builder

# 디버깅 모드
docker-compose --profile debug up debug

# 모니터링 포함
docker-compose --profile monitor up monitor

# 디버깅 + 모니터링
docker-compose --profile debug --profile monitor up
```

### 3. 수동 Docker 명령
```bash
# 이미지 빌드
docker build -t rpi4-boot-builder .

# 컨테이너 실행 (지속적)
docker run -d --name rpi4-builder-persistent \
    --privileged \
    -v $(pwd):/output \
    rpi4-boot-builder \
    sleep infinity

# 빌드 실행
docker exec rpi4-builder-persistent /rpi-boot/build_all.sh
```

## 📊 빌드 결과

성공적인 빌드 후 다음 파일들이 생성됩니다:

- `rpi4-complete.img` (153MB) - 완전한 부팅 이미지
- `output/kernel8.img` - ARM64 커널 바이너리
- `output/config.txt` - 라즈베리파이 부트 설정

## 🔧 시스템 요구사항

| 구성 요소 | 최소 | 권장 |
|----------|------|------|
| RAM | 8GB | 16GB |
| CPU | 4코어 | 8코어+ |
| 디스크 | 20GB | 50GB |
| Docker | 20.10+ | 최신 |

## 📖 상세 문서

- [`docs/complete-build-experience.md`](docs/complete-build-experience.md) - 전체 빌드 과정 상세 가이드
- [`docs/troubleshooting-guide.md`](docs/troubleshooting-guide.md) - 문제 해결 가이드
- [`CLAUDE.md`](CLAUDE.md) - 프로젝트 컨텍스트 및 개발 히스토리

## ⚡ 성능 최적화

### 빌드 시간
- **예상 시간**: 36분 (8코어, 15GB RAM 환경)
- **최적화 목표**: 25분 이하

### Docker 리소스 설정
```yaml
# docker-compose.yml에서 조정
resources:
  limits:
    memory: 12G    # 사용 가능한 RAM에 따라 조정
    cpus: '8'      # CPU 코어 수에 따라 조정
```

## 🎯 주요 특징

- ✅ **컨테이너 지속성**: 빌드 진행상황 보존
- ✅ **자동 오류 복구**: 일반적인 빌드 오류 자동 해결
- ✅ **실시간 모니터링**: 빌드 상태 실시간 확인
- ✅ **Docker 최적화**: 멀티 서비스 환경 지원
- ✅ **완전 자동화**: 클릭 한 번으로 완성된 이미지 생성

## 📝 SD 카드 플래싱

```bash
# Linux/macOS
sudo dd if=rpi4-complete.img of=/dev/sdX bs=4M status=progress

# Windows (WSL2)
# 또는 Raspberry Pi Imager 사용 권장
```

## 🆘 문제 해결

문제가 발생하면:

1. `build.log` 파일 확인
2. 시스템 리소스 상태 점검 (`free -h`, `df -h`)
3. Docker 상태 확인 (`docker ps`, `docker system df`)
4. [troubleshooting-guide.md](docs/troubleshooting-guide.md) 참조

---

**최종 업데이트**: 2025-07-27  
**테스트 환경**: WSL2, Docker, Ubuntu 22.04  
**빌드 성공률**: 100% (36분 평균)<!-- Last updated: Sun Jul 27 09:55:12 KST 2025 -->
