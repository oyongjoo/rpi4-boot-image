#!/usr/bin/env python3
"""
RPi4 부팅 이미지 자동 빌드 스크립트 (오류 자동 수정 기능 + 컨테이너 유지)
- Docker 컨테이너 유지하면서 빌드 진행
- 오류 발생 시 컨테이너 내부에서 자동 복구
- 빌드 진행상황 보존
- 최종 rpi4-complete.img 생성까지 완전 자동화
"""

import subprocess
import time
import re
import os
import signal
import json
from datetime import datetime

class AutoRPi4Builder:
    def __init__(self):
        self.container_name = "rpi4-builder-persistent"
        self.image_name = "rpi4-boot-builder"
        self.build_log = "build_progress.log"
        self.error_patterns = {
            "memory": [r"fatal: out of memory", r"Cannot allocate memory", r"killed"],
            "disk": [r"No space left on device", r"Disk full"],
            "network": [r"unable to connect", r"Network is unreachable", r"timeout"],
            "permission": [r"Permission denied", r"Operation not permitted"],
            "compile": [r"error:", r"failed", r"make.*Error"],
            "docker": [r"docker.*error", r"container.*not found"]
        }
        
    def log(self, message, level="INFO"):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[94m",     # 파란색
            "SUCCESS": "\033[92m",  # 초록색  
            "WARNING": "\033[93m",  # 노란색
            "ERROR": "\033[91m",    # 빨간색
            "RESET": "\033[0m"      # 리셋
        }
        
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{timestamp}] {message}{colors['RESET']}")
        
        # 파일에도 로그 저장
        with open(self.build_log, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def run_command(self, command, capture_output=True):
        """명령어 실행"""
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(command, shell=True)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
    
    def check_container_exists(self):
        """컨테이너 존재 확인"""
        success, stdout, _ = self.run_command(f"docker ps -a --filter name={self.container_name} --format '{{{{.Names}}}}'")
        return success and self.container_name in stdout
    
    def check_container_running(self):
        """컨테이너 실행 상태 확인"""
        success, stdout, _ = self.run_command(f"docker ps --filter name={self.container_name} --format '{{{{.Names}}}}'")
        return success and self.container_name in stdout
    
    def start_or_create_container(self):
        """컨테이너 시작 또는 생성"""
        if self.check_container_exists():
            if not self.check_container_running():
                self.log(f"기존 컨테이너 {self.container_name} 시작...", "INFO")
                success, _, stderr = self.run_command(f"docker start {self.container_name}")
                if not success:
                    self.log(f"컨테이너 시작 실패: {stderr}", "ERROR")
                    return False
            else:
                self.log(f"컨테이너 {self.container_name} 이미 실행 중", "INFO")
        else:
            self.log(f"새 컨테이너 {self.container_name} 생성...", "INFO")
            create_cmd = f"""docker run -d --name {self.container_name} \
                --privileged \
                -v $(pwd):/output \
                {self.image_name} \
                sleep infinity"""
            
            success, _, stderr = self.run_command(create_cmd)
            if not success:
                self.log(f"컨테이너 생성 실패: {stderr}", "ERROR")
                return False
        
        # 컨테이너가 정상 동작하는지 확인
        time.sleep(2)
        success, _, _ = self.run_command(f"docker exec {self.container_name} echo 'Container Ready'")
        if success:
            self.log("✅ 컨테이너 준비 완료", "SUCCESS")
            return True
        else:
            self.log("❌ 컨테이너 준비 실패", "ERROR")
            return False
    
    def execute_in_container(self, command, show_output=False):
        """컨테이너 내부에서 명령어 실행"""
        docker_cmd = f"docker exec {self.container_name} bash -c '{command}'"
        
        if show_output:
            # 실시간 출력을 위한 스트리밍 실행
            process = subprocess.Popen(
                docker_cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            output_lines = []
            while True:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())  # 실시간 출력
                    output_lines.append(line)
                elif process.poll() is not None:
                    break
            
            return_code = process.poll()
            full_output = ''.join(output_lines)
            return return_code == 0, full_output, ""
        else:
            return self.run_command(docker_cmd, capture_output=True)
    
    def detect_error_type(self, stderr):
        """오류 유형 감지"""
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, stderr, re.IGNORECASE):
                    return error_type
        return "unknown"
    
    def auto_fix_error(self, error_type, stderr):
        """오류 자동 수정"""
        self.log(f"🔧 {error_type} 오류 자동 수정 시도...", "WARNING")
        
        if error_type == "memory":
            # 메모리 정리 및 스왑 사용
            self.execute_in_container("sync && echo 3 > /proc/sys/vm/drop_caches")
            self.execute_in_container("swapoff -a && swapon -a")
            return True
            
        elif error_type == "disk":
            # 임시 파일 정리
            self.execute_in_container("find /tmp -type f -atime +1 -delete")
            self.execute_in_container("apt-get clean")
            return True
            
        elif error_type == "network":
            # 네트워크 재시도
            time.sleep(5)
            return True
            
        elif error_type == "permission":
            # 권한 설정
            self.execute_in_container("chmod -R 755 /rpi-boot")
            return True
            
        elif error_type == "compile":
            # 컴파일 환경 정리 및 누락된 의존성 설치
            if "You must install" in stderr and "/usr/bin/file" in stderr:
                self.log("🔧 누락된 'file' 패키지 설치 중...", "WARNING")
                self.execute_in_container("apt-get update && apt-get install -y file")
            elif "You must install" in stderr:
                # 다른 누락된 패키지들도 처리
                self.execute_in_container("apt-get update && apt-get install -y build-essential")
            else:
                # 기본 컴파일 환경 정리
                self.execute_in_container("cd /rpi-boot/linux && make clean")
            return True
            
        return False
    
    def run_build_step(self, step_name, command, max_retries=3, show_output=True):
        """빌드 단계 실행 (재시도 포함)"""
        self.log(f"🔨 {step_name} 시작...", "INFO")
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"재시도 {attempt}/{max_retries-1}...", "WARNING")
            
            # 실시간 출력 표시
            success, stdout, stderr = self.execute_in_container(command, show_output=show_output)
            
            if success:
                self.log(f"✅ {step_name} 완료", "SUCCESS")
                return True
            else:
                error_type = self.detect_error_type(stderr if stderr else stdout)
                self.log(f"❌ {step_name} 실패: {error_type} 오류", "ERROR")
                
                # 자동 수정 시도
                if self.auto_fix_error(error_type, stderr if stderr else stdout):
                    time.sleep(2)
                    continue
                else:
                    break
        
        self.log(f"❌ {step_name} 최종 실패", "ERROR")
        return False
    
    def run_full_build(self):
        """전체 빌드 실행"""
        # 컨테이너 준비
        if not self.start_or_create_container():
            return False
        
        # 빌드 스크립트를 컨테이너에 복사
        self.run_command(f"docker cp auto_build.sh {self.container_name}:/rpi-boot/")
        
        # 빌드 실행
        build_steps = [
            ("커널 빌드", """
                cd /rpi-boot/linux
                make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- bcm2711_defconfig
                echo 'CONFIG_NETFILTER=y' >> .config
                echo 'CONFIG_IPTABLES=y' >> .config
                make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
                make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) Image modules dtbs
            """),
            ("Buildroot 빌드", """
                cd /rpi-boot/buildroot
                echo "pi -1 pi -1 =raspberry /home/pi /bin/bash sudo" > board/users_table.txt
                make raspberrypi4_64_defconfig
                echo 'BR2_PACKAGE_OPENSSH=y' >> .config
                echo 'BR2_PACKAGE_SUDO=y' >> .config
                echo 'BR2_SYSTEM_ROOT_PASSWORD="raspberry"' >> .config
                echo 'BR2_ROOTFS_USERS_TABLES="board/users_table.txt"' >> .config
                make olddefconfig
                make -j$(nproc)
            """),
            ("이미지 생성", """
                cd /rpi-boot
                bash /rpi-boot/auto_build.sh
            """)
        ]
        
        for step_name, command in build_steps:
            if not self.run_build_step(step_name, command):
                return False
        
        # 결과물 복사
        self.execute_in_container("cp /rpi-boot/rpi4-complete.img /output/ 2>/dev/null || true")
        
        return True
    
    def cleanup(self, force_remove=False):
        """정리 (컨테이너는 유지)"""
        if force_remove:
            self.log("🗑️ 컨테이너 강제 삭제...", "WARNING")
            self.run_command(f"docker rm -f {self.container_name}")
        else:
            self.log("💾 컨테이너 유지 (다음 빌드에서 재사용)", "INFO")
    
    def run(self):
        """메인 실행"""
        self.log("🚀 RPi4 자동 빌드 시스템 시작 (컨테이너 유지 모드)", "SUCCESS")
        
        try:
            success = self.run_full_build()
            
            if success:
                self.log("🎉 모든 작업이 성공적으로 완료되었습니다!", "SUCCESS")
            else:
                self.log("❌ 빌드 작업이 실패했습니다", "ERROR")
                
            return success
            
        except KeyboardInterrupt:
            self.log("⚠️ 사용자에 의해 중단됨", "WARNING")
            return False
        finally:
            # 사용자 중단 시에는 컨테이너 유지 (변경사항 보존)
            self.cleanup(force_remove=False)

if __name__ == "__main__":
    builder = AutoRPi4Builder()
    success = builder.run()
    exit(0 if success else 1)