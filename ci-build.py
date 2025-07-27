#!/usr/bin/env python3
"""
RPi4 CI/CD 전용 빌드 스크립트
- GitHub Actions 환경 최적화
- 타임아웃 및 리소스 제한 고려
- 아티팩트 자동 생성
"""

import subprocess
import time
import os
import sys
import json
from datetime import datetime
from pathlib import Path

class CIRPi4Builder:
    def __init__(self):
        self.container_name = "rpi4-builder-ci"
        self.image_name = "rpi4-boot-builder"
        self.build_log = "build.log"
        self.is_ci = os.getenv('CI', 'false').lower() == 'true'
        self.max_build_time = int(os.getenv('MAX_BUILD_TIME', '7200'))  # 2시간
        
    def log(self, message, level="INFO"):
        """CI 친화적 로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # GitHub Actions 그룹 지원
        if level == "ERROR":
            print(f"::error::{message}")
        elif level == "WARNING":
            print(f"::warning::{message}")
        else:
            print(f"[{timestamp}] {message}")
            
        # 로그 파일에도 저장
        with open(self.build_log, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def run_command(self, command, timeout=None):
        """명령 실행 (타임아웃 지원)"""
        self.log(f"실행: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.log(f"명령 타임아웃: {command}", "ERROR")
            return False, "", "Timeout"
    
    def cleanup_old_containers(self):
        """이전 CI 컨테이너 정리"""
        self.log("🧹 이전 CI 컨테이너 정리 중...")
        
        # 기존 컨테이너 중단 및 삭제
        subprocess.run(f"docker rm -f {self.container_name}", shell=True, capture_output=True)
        
        # 불필요한 이미지 정리 (CI 환경 공간 절약)
        if self.is_ci:
            subprocess.run("docker system prune -f", shell=True, capture_output=True)
    
    def build_docker_image(self):
        """Docker 이미지 빌드"""
        self.log("🐳 Docker 이미지 빌드 중...")
        
        success, stdout, stderr = self.run_command(
            f"docker build -t {self.image_name}:latest .",
            timeout=1800  # 30분 제한
        )
        
        if not success:
            self.log(f"Docker 빌드 실패: {stderr}", "ERROR")
            return False
            
        self.log("✅ Docker 이미지 빌드 완료")
        return True
    
    def start_build_container(self):
        """빌드 컨테이너 시작"""
        self.log("🚀 빌드 컨테이너 시작 중...")
        
        # CI 환경에 최적화된 컨테이너 실행
        docker_cmd = f"""docker run -d --name {self.container_name} \
            --privileged \
            -v $(pwd):/output \
            -e CI=true \
            -e DEBIAN_FRONTEND=noninteractive \
            {self.image_name}:latest \
            sleep infinity"""
            
        success, stdout, stderr = self.run_command(docker_cmd)
        
        if not success:
            self.log(f"컨테이너 시작 실패: {stderr}", "ERROR")
            return False
            
        # 컨테이너 준비 대기
        time.sleep(5)
        self.log("✅ 빌드 컨테이너 준비 완료")
        return True
    
    def execute_build(self):
        """실제 빌드 실행"""
        self.log("🔨 RPi4 커널 빌드 시작...")
        
        # CI 최적화된 빌드 명령
        build_script = """
        set -e
        echo "=== 빌드 시작 ===" 
        cd /rpi-boot
        
        # 병렬 빌드 수 조정 (CI 환경)
        NPROC=$(nproc)
        if [ "$NPROC" -gt 4 ]; then
            NPROC=4  # CI 환경에서는 4개로 제한
        fi
        
        echo "병렬 빌드 수: $NPROC"
        
        # Linux 커널 빌드
        echo "=== 커널 빌드 ===" 
        cd linux
        make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- bcm2711_defconfig
        echo 'CONFIG_NETFILTER=y' >> .config
        echo 'CONFIG_IPTABLES=y' >> .config
        make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
        
        # 타임아웃 대비 핵심만 빌드
        make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$NPROC Image dtbs
        
        # Buildroot 빌드
        echo "=== Buildroot 빌드 ===" 
        cd ../buildroot
        make raspberrypi4_64_defconfig
        
        # 패키지 설정
        echo 'BR2_PACKAGE_OPENSSH=y' >> .config
        echo 'BR2_PACKAGE_SUDO=y' >> .config
        echo 'BR2_PACKAGE_NANO=y' >> .config
        echo 'BR2_PACKAGE_BASH=y' >> .config
        echo 'BR2_ROOTFS_POST_BUILD_SCRIPT="board/raspberrypi/post-build.sh"' >> .config
        echo 'BR2_ROOTFS_POST_IMAGE_SCRIPT="board/raspberrypi/post-image.sh"' >> .config
        
        make olddefconfig
        make -j$NPROC
        
        # 최종 이미지 생성
        echo "=== 이미지 생성 ===" 
        cp output/images/sdcard.img /output/rpi4-complete.img
        
        echo "=== 빌드 완료 ===" 
        ls -lh /output/rpi4-complete.img
        """
        
        # 빌드 실행 (긴 타임아웃)
        success, stdout, stderr = self.run_command(
            f'docker exec {self.container_name} bash -c "{build_script}"',
            timeout=self.max_build_time
        )
        
        if success:
            self.log("✅ 빌드 성공!")
            return True
        else:
            self.log(f"❌ 빌드 실패: {stderr}", "ERROR")
            return False
    
    def verify_build(self):
        """빌드 결과 검증"""
        self.log("🔍 빌드 결과 검증 중...")
        
        if not os.path.exists("rpi4-complete.img"):
            self.log("이미지 파일이 없습니다", "ERROR")
            return False
        
        # 파일 크기 검증
        size = os.path.getsize("rpi4-complete.img")
        min_size = 50 * 1024 * 1024   # 50MB
        max_size = 300 * 1024 * 1024  # 300MB
        
        if size < min_size or size > max_size:
            self.log(f"이미지 크기 이상: {size} bytes", "ERROR")
            return False
        
        self.log(f"✅ 이미지 검증 성공: {size} bytes")
        return True
    
    def generate_build_stats(self):
        """빌드 통계 생성"""
        stats = {
            "build_time": datetime.now().isoformat(),
            "image_size": os.path.getsize("rpi4-complete.img") if os.path.exists("rpi4-complete.img") else 0,
            "ci_environment": self.is_ci,
            "build_number": os.getenv('GITHUB_RUN_NUMBER', 'local'),
            "commit_sha": os.getenv('GITHUB_SHA', 'unknown')
        }
        
        with open("build-stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        
        self.log("📊 빌드 통계 생성 완료")
    
    def cleanup(self):
        """정리 작업"""
        self.log("🧹 정리 작업 중...")
        
        # 컨테이너 로그 저장
        if os.path.exists(f"/tmp/{self.container_name}.log"):
            subprocess.run(
                f"docker logs {self.container_name} > container-build.log",
                shell=True, capture_output=True
            )
        
        # 컨테이너 정리 (CI 환경에서만)
        if self.is_ci:
            subprocess.run(f"docker rm -f {self.container_name}", shell=True, capture_output=True)
    
    def build(self):
        """전체 빌드 프로세스"""
        start_time = time.time()
        
        try:
            self.log("🚀 CI/CD RPi4 빌드 시작")
            
            # 1. 환경 정리
            self.cleanup_old_containers()
            
            # 2. Docker 이미지 빌드
            if not self.build_docker_image():
                return False
            
            # 3. 빌드 컨테이너 시작
            if not self.start_build_container():
                return False
            
            # 4. 실제 빌드 실행
            if not self.execute_build():
                return False
            
            # 5. 결과 검증
            if not self.verify_build():
                return False
            
            # 6. 통계 생성
            self.generate_build_stats()
            
            build_time = time.time() - start_time
            self.log(f"🎉 전체 빌드 완료! 소요시간: {build_time:.1f}초")
            
            return True
            
        except Exception as e:
            self.log(f"빌드 중 예외 발생: {e}", "ERROR")
            return False
        finally:
            self.cleanup()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("CI/CD RPi4 빌드 스크립트")
        print("사용법: python3 ci-build.py")
        print("환경변수:")
        print("  CI=true              # CI 환경 표시")
        print("  MAX_BUILD_TIME=7200  # 최대 빌드 시간(초)")
        return
    
    builder = CIRPi4Builder()
    success = builder.build()
    
    if success:
        print("✅ 빌드 성공")
        sys.exit(0)
    else:
        print("❌ 빌드 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()