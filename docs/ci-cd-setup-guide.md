# CI/CD 설정 가이드

## 🎯 개요
매일 자동으로 RPi4 커널을 빌드하고 테스트하는 CI/CD 파이프라인 구성 가이드입니다.

---

## 🛠️ 1. GitHub Actions 설정

### Repository Secrets 설정
GitHub 저장소 Settings → Secrets and variables → Actions에서 다음 설정:

#### 필수 설정
```
# 알림용 (선택사항)
TELEGRAM_BOT_TOKEN=1234567890:AAAA...    # 텔레그램 봇 토큰
TELEGRAM_CHAT_ID=-1001234567890          # 텔레그램 채팅 ID
DISCORD_WEBHOOK_URL=https://discord...   # Discord 웹훅 URL
```

#### 텔레그램 봇 설정 방법
1. **봇 생성**:
   ```
   1. @BotFather와 대화 시작
   2. /newbot 명령어 입력
   3. 봇 이름 설정 (예: RPi4 Build Bot)
   4. 봇 사용자명 설정 (예: rpi4_build_bot)
   5. 받은 토큰을 TELEGRAM_BOT_TOKEN에 저장
   ```

2. **Chat ID 확인**:
   ```bash
   # 봇과 메시지를 주고받은 후
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   # 결과에서 "chat":{"id": 숫자}를 찾아서 TELEGRAM_CHAT_ID에 저장
   ```

### Repository Variables 설정
Actions → Variables에서 빌드 설정:

```
MAX_BUILD_TIME=7200        # 최대 빌드 시간 (초)
BUILD_SCHEDULE=0 2 * * *   # 빌드 스케줄 (매일 오전 2시 UTC)
NOTIFICATION_ENABLED=true  # 알림 활성화
```

---

## 📅 2. 빌드 스케줄 설정

### 기본 스케줄
```yaml
# 매일 오전 2시 (UTC) = 한국시간 오전 11시
schedule:
  - cron: '0 2 * * *'
```

### 다른 스케줄 예시
```yaml
# 매주 월요일 오전 1시
- cron: '0 1 * * MON'

# 매일 오전 6시, 오후 6시
- cron: '0 6,18 * * *'

# 평일만 매일 오전 3시
- cron: '0 3 * * 1-5'
```

---

## 🔧 3. 로컬 테스트 방법

### CI 스크립트 로컬 테스트
```bash
# CI 모드로 빌드 테스트
export CI=true
export MAX_BUILD_TIME=3600
python3 ci-build.py

# 결과 확인
ls -la rpi4-complete.img
cat build-stats.json
```

### Docker 환경에서 테스트
```bash
# GitHub Actions 환경 시뮬레이션
docker run --rm -v $(pwd):/workspace -w /workspace \
  -e CI=true \
  -e GITHUB_RUN_NUMBER=123 \
  ubuntu:22.04 \
  bash -c "apt update && apt install -y python3 docker.io && python3 ci-build.py"
```

---

## 📊 4. 모니터링 및 알림

### 빌드 상태 확인
```bash
# GitHub CLI로 워크플로우 상태 확인
gh run list --workflow=daily-build.yml

# 특정 실행 로그 확인
gh run view <run-id> --log
```

### 알림 테스트
```bash
# 텔레그램 알림 테스트
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
  -d chat_id="<CHAT_ID>" \
  -d text="🧪 CI/CD 테스트 메시지"

# Discord 웹훅 테스트
curl -H "Content-Type: application/json" \
  -X POST \
  -d '{"content":"🧪 CI/CD 테스트 메시지"}' \
  "<DISCORD_WEBHOOK_URL>"
```

---

## 🎯 5. 고급 설정

### 조건부 빌드
소스코드 변경이 있을 때만 빌드:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'
  push:
    paths:
      - 'Dockerfile'
      - 'build.py'
      - 'ci-build.py'
      - '.github/workflows/**'
```

### 멀티 아키텍처 빌드
```yaml
strategy:
  matrix:
    arch: [amd64, arm64]
    include:
      - arch: amd64
        runner: ubuntu-latest
      - arch: arm64
        runner: buildjet-4vcpu-ubuntu-2204-arm
```

### 캐시 최적화
```yaml
- name: 고급 빌드 캐시
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/docker
      ./cache/linux-source
      ./cache/buildroot-dl
    key: rpi4-cache-v2-${{ hashFiles('**/Dockerfile', '**/ci-build.py') }}
```

---

## 📈 6. 성능 최적화

### GitHub Actions 러너 최적화
```yaml
# 더 큰 러너 사용 (GitHub Pro 계정 필요)
runs-on: ubuntu-latest-8-cores

# 또는 자체 호스팅 러너
runs-on: self-hosted
```

### 빌드 시간 단축
```bash
# 병렬 빌드 최적화
export MAKEFLAGS="-j$(nproc)"

# ccache 사용
export USE_CCACHE=1
export CCACHE_DIR=/tmp/ccache
```

---

## 📋 7. 문제 해결

### 일반적인 문제들

#### 빌드 타임아웃
```yaml
# 워크플로우 타임아웃 증가
timeout-minutes: 180  # 3시간

# 또는 단계별 타임아웃
- name: 빌드 실행
  timeout-minutes: 120
```

#### 디스크 공간 부족
```bash
# 더 적극적인 정리
sudo rm -rf /usr/local/lib/android
sudo rm -rf /usr/local/.ghcup
sudo rm -rf /usr/local/share/powershell
sudo rm -rf /usr/local/share/chromium
sudo apt-get autoremove -y
sudo apt-get autoclean
```

#### 메모리 부족
```yaml
# 스왑 메모리 추가
- name: 스왑 메모리 설정
  run: |
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
```

### 로그 분석
```bash
# 빌드 실패 원인 분석
grep -i error build.log
grep -i failed build.log

# 메모리 사용량 확인
grep -i "killed\|memory\|oom" build.log
```

---

## 🎉 8. 완성된 CI/CD 구조

```
프로젝트/
├── .github/workflows/
│   └── daily-build.yml      # 메인 워크플로우
├── ci-build.py              # CI 전용 빌드 스크립트
├── build.py                 # 로컬 개발용 빌드
├── Dockerfile               # 빌드 환경
├── docs/
│   └── ci-cd-setup-guide.md # 이 문서
└── README.md               # 전체 가이드
```

### 예상 CI/CD 플로우
```
매일 오전 2시 (UTC)
    ↓
환경 정리 및 Docker 빌드
    ↓
RPi4 커널 빌드 (36분)
    ↓
이미지 검증
    ↓
아티팩트 업로드
    ↓
텔레그램/Discord 알림
    ↓
30일 후 자동 정리
```

---

## 📞 추가 지원

문제 발생 시:
1. [GitHub Issues](https://github.com/your-repo/issues)에 문제 보고
2. 빌드 로그와 함께 상세 정보 제공
3. `build-stats.json` 파일 첨부

## 💰 GitHub Actions 무료 제공의 놀라운 가치

### 🎁 Public 리포지토리 혜택 (현재 적용)
- **컴퓨팅 시간**: **무제한** ⭐ (Linux 빌드)
- **스토리지**: 500MB (아티팩트 저장)
- **동시 작업**: 20개
- **하드웨어**: 2코어 CPU, 7GB RAM, 14GB SSD

### 💸 실제 경제적 가치
**RPi4 커널 빌드 1회 = 60분 소요**
- AWS EC2 t3.medium: $0.05/빌드
- Google Cloud e2-standard-2: $0.07/빌드
- **월 30회 자동 빌드**: $1.5-2.1/월 상당 **→ 완전 무료!**

### 🏢 Microsoft/GitHub의 전략
1. **개발자 생태계 확장**: 오픈소스 프로젝트 활성화
2. **Azure 인프라 홍보**: 클라우드 기술 체험 기회
3. **개발자 락인**: GitHub 생태계 의존성 증가
4. **데이터 수집**: 개발 트렌드 및 기술 스택 분석

### 🎯 우리 프로젝트의 혜택
- ✅ **매일 60분 빌드** = 월 30시간 무료 컴퓨팅
- ✅ **전문 클라우드 인프라** 활용
- ✅ **자동 결과물 관리** (30일간 저장)
- ✅ **완전한 CI/CD 파이프라인** 무료 구축

**결론**: 개발자에게는 정말 **황금 같은 시대**! 🚀

---

**예상 비용**: **완전 무료** (Public 리포지토리 기준, Linux 빌드 무제한)