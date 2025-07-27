# 라즈베리파이 4 커널 빌드 프로젝트 컨텍스트

## 프로젝트 개요
이 프로젝트는 라즈베리파이 4용 완전한 부팅 이미지를 Docker 환경에서 빌드하는 시스템입니다.

### 주요 구성요소
- **Linux 커널 6.6** (라즈베리파이 전용 버전)
- **Buildroot 루트파일시스템** (최소 환경 + pi 사용자)
- **완전한 부팅 이미지** (2GB, 파티션 포함)

## 빌드 환경
- **플랫폼**: Docker (linux/amd64)
- **베이스 이미지**: Ubuntu 22.04
- **크로스 컴파일**: aarch64-linux-gnu (ARM64)
- **타겟 하드웨어**: 라즈베리파이 4 (BCM2711)

## 자동화 스크립트
### `smart_build.py` - 지능형 빌드 시스템 v2.0
```bash
python3 smart_build.py                  # 기본 빌드 (스마트 재시작)
python3 smart_build.py --clean          # 이전 결과물 정리 후 빌드
python3 smart_build.py --no-resume      # 재시작 없이 처음부터 빌드
python3 smart_build.py --max-attempts 10 --monitor-interval 60  # 고급 옵션
```

**핵심 기능:**
- **실시간 모니터링**: 2분마다 빌드 상태 점검
- **지능형 오류 감지**: 6가지 오류 유형 자동 감지
- **자동 복구 시스템**: 오류별 맞춤 복구 전략
- **빌드 재시도**: 최대 5회 자동 재시도 (설정 가능)
- **상세 로그 분석**: 오류 컨텍스트 및 통계 제공
- **Docker 자동 관리**: 컨테이너 생성/실행/정리

**감지/복구 가능한 오류:**
- 메모리 부족 → Docker 정리, 스왑 확인
- 디스크 공간 부족 → 이미지/임시파일 정리
- 네트워크 오류 → 연결 테스트, 재시도
- Docker 오류 → 서비스 재시작, 시스템 정리
- 컴파일 오류 → 빌드 옵션 조정
- 권한 오류 → 설정 안내

## 빌드 결과물
### 주요 파일
- `output/rpi4-complete.img` - 완전한 부팅 이미지 (2GB)
- `output/kernel8.img` - 커널 바이너리
- `output/config.txt` - 부트 설정 파일
- `build.log` - 전체 빌드 로그

### 이미지 구조
- **부트 파티션**: 256MB FAT32 (커널, 펌웨어, 설정)
- **루트 파티션**: ~1.7GB EXT4 (Buildroot 파일시스템)

## 사용자 계정
- **pi 사용자**: 비밀번호 `raspberry`, sudo 권한
- **root 사용자**: 비밀번호 `raspberry`
- **SSH**: 기본 활성화

## 주요 특징
### 하드웨어 설정
- ARM64 아키텍처 (64비트)
- GPU 메모리: 128MB
- 오버클록: CPU 1.8GHz, GPU 600MHz
- HDMI 출력: 1920x1080

### 네트워크 기능
- WiFi/Bluetooth 지원 (드라이버 포함)
- SSH, 무선 도구들 (hostapd, wpa_supplicant 등)
- 네트워킹 유틸리티 (iptables, iproute2 등)

## 빌드 시간
- **예상 소요시간**: 30-60분 (하드웨어 성능에 따라)
- **주요 단계**: 커널 컴파일 (가장 오래 소요), Buildroot 빌드, 이미지 생성

## 문제 해결
### 로그 확인
- `build.log`: 전체 빌드 과정 로그
- Docker 빌드 단계별 로그 포함

### 일반적인 문제
1. **메모리 부족**: Docker 메모리 할당 증가 필요
2. **권한 문제**: 스크립트 실행 권한 확인
3. **디스크 공간**: 최소 8GB 여유 공간 필요

## SD 카드 플래싱
```bash
sudo dd if=output/rpi4-complete.img of=/dev/sdX bs=4M status=progress
```
**주의**: /dev/sdX는 실제 SD 카드 장치명으로 변경

## 현재 빌드 상태 (2025-07-26)

### 완료된 작업
- ✅ **기본 Dockerfile 작성**: 커널 6.6 + Buildroot + 네트워킹 기능
- ✅ **의존성 문제 해결**: readline, openssl, zlib, libcrypt 추가
- ✅ **네트워킹 기능 강화**: iptables, hostapd, wpa_supplicant, NL80211 지원
- ✅ **Broadcom WiFi/BT 비활성화**: 기본 WiFi/BT 모듈 비활성화
- ✅ **문서화 시스템**: 자동 빌드 문제 추적 (`build_issues_and_fixes.md`)
- ✅ **smart_build.py 개선**: 자동 문서 업데이트 기능 추가

### 설정된 패키지들
**네트워킹:**
- BR2_PACKAGE_IPTABLES=y (방화벽)
- BR2_PACKAGE_IPROUTE2=y (고급 라우팅)
- BR2_PACKAGE_DHCP=y / BR2_PACKAGE_DHCPCD=y (DHCP 서버/클라이언트)
- BR2_PACKAGE_BRIDGE_UTILS=y (브리지 네트워크)

**WiFi 관련:**
- BR2_PACKAGE_HOSTAPD=y (AP 모드)
- BR2_PACKAGE_WPA_SUPPLICANT=y + NL80211 지원
- BR2_PACKAGE_WIRELESS_TOOLS=y / BR2_PACKAGE_IW=y (무선 도구)

**커널 기능:**
- CONFIG_NETFILTER=y / CONFIG_NF_TABLES=y (방화벽)
- CONFIG_CFG80211=y / CONFIG_MAC80211=y (무선 스택)
- CONFIG_BRIDGE=y / CONFIG_VLAN_8021Q=y (네트워크 기능)

### 현재 진행 상황 (2025-07-27)

✅ **완료된 작업들:**
- **GitHub 리포지토리 구축**: https://github.com/oyongjoo/rpi4-boot-image (Public)
- **CI/CD 파이프라인 구성**: 매일 자동 빌드 (.github/workflows/daily-build.yml)
- **Docker 컨테이너 지속성 문제 해결**: `--rm` 제거, `sleep infinity` 활용
- **빌드 스크립트 통일**: `build.py` (메인), `ci-build.py` (CI 전용)
- **실시간 모니터링 구현**: 36분 빌드 과정 실시간 추적
- **성공적인 로컬 빌드**: 153MB 완전한 부팅 이미지 생성

🚀 **GitHub Actions 자동화 시스템:**
- **매일 자동 빌드**: 오전 2시 UTC (한국시간 11시) 실행
- **완전 무료**: Public 리포지토리로 무제한 Linux 빌드 혜택
- **아티팩트 자동 관리**: 30일간 이미지 파일 보관
- **알림 시스템**: 텔레그램/Discord 빌드 결과 알림 (선택사항)

💰 **GitHub Actions의 놀라운 경제적 가치:**
- **월 30회 60분 빌드** = AWS 기준 $1.5-2.1/월 상당 → **완전 무료!**
- **전문 클라우드 인프라**: 2코어 CPU, 7GB RAM, 14GB SSD 무료 활용
- **Microsoft/GitHub 전략**: 개발자 생태계 확장 및 Azure 홍보 효과

## 향후 추가할 기능 (TODO)

### 빌드 완료 알림 시스템
```python
# 텔레그램 봇 알림 추가 예정
def send_telegram_notification(message):
    bot_token = "BOT_TOKEN"  # @BotFather에서 생성
    chat_id = "CHAT_ID"      # getUpdates로 확인
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

# 사용법:
# 1. 텔레그램에서 @BotFather 검색
# 2. /newbot 명령어로 봇 생성
# 3. 봇 토큰 받기
# 4. 봇과 대화 시작 후 Chat ID 확인
# 5. smart_build.py에 알림 기능 통합
```

**다른 알림 옵션:**
- Discord 웹훅 알림
- 이메일 알림 (SMTP)
- 시스템 데스크톱 알림
- Slack 웹훅

### 성능 최적화
- 멀티스레드 컴파일 옵션 조정
- Docker 리소스 제한 최적화
- 빌드 캐시 활용 개선

## 확장 가능성
- 추가 패키지 설치: Buildroot 설정 수정
- 커널 옵션 변경: Dockerfile의 config 섹션 수정
- 성능 튜닝: config.txt 오버클록 설정 조정

---
*이 컨텍스트는 Claude Code에서 자동으로 관리됩니다. 프로젝트 변경 시 업데이트하세요.*
*마지막 업데이트: 2025-07-27*
*GitHub 리포지토리: https://github.com/oyongjoo/rpi4-boot-image*