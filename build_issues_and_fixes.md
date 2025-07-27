# 빌드과정에서 발생한 문제점과 수정내용

## 문서 정보
- 작성일: 2025-07-26 (토요일)
- 프로젝트: 라즈베리파이 4 부팅 이미지 빌드
- 커널 버전: Linux 6.6.x
- 빌드 시스템: Docker + Buildroot

## 빌드 진행 상황

### 1단계: 초기 빌드 시도 (실패)
**시간**: 2025-07-26 01:00 ~ 06:00

**발생한 문제들**:

#### 문제 1: Buildroot readline 의존성 에러
```
Makefile:574: *** readline is in the dependency chain of bash that has added it to its _DEPENDENCIES variable without selecting it or depending on it from Config.in. Stop.
```

**원인**: Buildroot에서 bash 패키지를 활성화했지만 필수 의존성인 readline을 명시적으로 선택하지 않음

**수정내용**: Dockerfile에 `BR2_PACKAGE_READLINE=y` 추가
```dockerfile
echo 'BR2_PACKAGE_READLINE=y' >> .config && \
```

#### 문제 2: OpenSSL 의존성 에러
```
Makefile:574: *** openssl is in the dependency chain of openssh that has added it to its _DEPENDENCIES variable without selecting it or depending on it from Config.in. Stop.
```

**원인**: OpenSSH 패키지를 활성화했지만 필수 의존성인 OpenSSL을 명시적으로 선택하지 않음

**수정내용**: Dockerfile에 `BR2_PACKAGE_OPENSSL=y` 추가
```dockerfile
echo 'BR2_PACKAGE_OPENSSL=y' >> .config && \
```

### 2단계: 네트워킹 기능 추가
**시간**: 2025-07-26 06:30 ~

**추가된 기능들**:

#### 네트워킹 패키지들
- `BR2_PACKAGE_IPTABLES=y` - 방화벽 및 NAT 기능
- `BR2_PACKAGE_IPROUTE2=y` - 고급 네트워크 라우팅
- `BR2_PACKAGE_NET_TOOLS=y` - 기본 네트워크 도구 (ifconfig, netstat 등)
- `BR2_PACKAGE_DHCP=y` - DHCP 서버
- `BR2_PACKAGE_DHCPCD=y` - DHCP 클라이언트
- `BR2_PACKAGE_BRIDGE_UTILS=y` - 브리지 네트워크 유틸리티

#### WiFi 관련 패키지들
- `BR2_PACKAGE_HOSTAPD=y` - WiFi 액세스 포인트
- `BR2_PACKAGE_WPA_SUPPLICANT=y` - WiFi 클라이언트
- `BR2_PACKAGE_WPA_SUPPLICANT_NL80211=y` - NL80211 지원
- `BR2_PACKAGE_WIRELESS_TOOLS=y` - 무선 네트워크 도구
- `BR2_PACKAGE_IW=y` - 현대적인 무선 도구
- `BR2_PACKAGE_LIBNL=y` - Netlink 라이브러리

#### 커널 네트워킹 기능 활성화
```dockerfile
echo 'CONFIG_NETFILTER=y' >> .config && \
echo 'CONFIG_NF_TABLES=y' >> .config && \
echo 'CONFIG_NETFILTER_XTABLES=y' >> .config && \
echo 'CONFIG_NETFILTER_NETLINK=y' >> .config && \
echo 'CONFIG_NL80211_TESTMODE=y' >> .config && \
echo 'CONFIG_CFG80211=y' >> .config && \
echo 'CONFIG_CFG80211_DEBUGFS=y' >> .config && \
echo 'CONFIG_MAC80211=y' >> .config && \
echo 'CONFIG_MAC80211_DEBUGFS=y' >> .config && \
echo 'CONFIG_BRIDGE=y' >> .config && \
echo 'CONFIG_VLAN_8021Q=y' >> .config && \
```

#### Broadcom WiFi/BT 비활성화
```dockerfile
echo '# CONFIG_BRCMFMAC is not set' >> .config && \
echo '# CONFIG_BRCMUTIL is not set' >> .config && \
echo '# CONFIG_BT_HCIUART_BCM is not set' >> .config && \
echo '# CONFIG_BT_BCM is not set' >> .config && \
```

### 3단계: smart_build.py 스크립트 사용
**시간**: 2025-07-26 07:15 ~

**결정사항**: 수동 빌드에서 자동화된 빌드 스크립트로 전환
- 더 나은 에러 핸들링
- 실시간 모니터링
- 자동 재시도 기능

---

## 빌드 로그 추적

### 현재 진행 상황 (2025-07-26 07:15)
- 커널 컴파일 진행 중
- 무선 네트워크 드라이버 (ath6kl, mwifiex, rtw88 등) 컴파일 완료
- USB 호스트 드라이버 (DWC OTG) 컴파일 진행
- 터치스크린 드라이버 컴파일 중

### 예상되는 추가 문제점들
1. **메모리 부족**: 커널 컴파일 시 Docker 컨테이너 메모리 제한
2. **디스크 공간 부족**: 빌드 아티팩트로 인한 용량 부족
3. **타임아웃**: 긴 컴파일 시간으로 인한 타임아웃
4. **크로스 컴파일 에러**: ARM64 타겟 컴파일 시 도구체인 문제

---

*이 문서는 빌드 진행에 따라 실시간으로 업데이트됩니다.*