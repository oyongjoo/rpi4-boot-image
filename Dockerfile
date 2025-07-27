# RPi4 부트 이미지 빌드용 환경
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ARCH=arm64
ENV CROSS_COMPILE=aarch64-linux-gnu-
ENV KERNEL=kernel8

# 빌드 도구 설치 (재시도 로직 포함)
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    wget \
    unzip \
    dosfstools \
    kpartx \
    parted \
    util-linux \
    bc \
    bison \
    build-essential \
    flex \
    git \
    libssl-dev \
    libncurses5-dev \
    device-tree-compiler \
    xz-utils \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    libc6-dev-arm64-cross \
    vim \
    nano \
    curl \
    cpio \
    rsync \
    python3 \
    python3-pip \
    file \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ARM GCC 설치
RUN wget -O gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2 \
    "https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2" && \
    tar -xf gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2 -C /opt/ && \
    rm gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2

ENV PATH="/opt/gcc-arm-none-eabi-10.3-2021.10/bin:${PATH}"

WORKDIR /rpi-boot

# 소스 다운로드만 (빌드는 컨테이너 실행 시)
RUN wget -O firmware.zip https://github.com/raspberrypi/firmware/archive/refs/heads/master.zip && \
    unzip firmware.zip && \
    mv firmware-master firmware && \
    rm firmware.zip

RUN wget -O kernel.tar.gz https://github.com/raspberrypi/linux/archive/refs/heads/rpi-6.6.y.tar.gz && \
    tar -xzf kernel.tar.gz && \
    mv linux-rpi-6.6.y linux && \
    rm kernel.tar.gz

RUN wget -O buildroot.tar.gz https://github.com/buildroot/buildroot/archive/refs/tags/2024.02.7.tar.gz && \
    tar -xzf buildroot.tar.gz && \
    mv buildroot-2024.02.7 buildroot && \
    rm buildroot.tar.gz

# 빌드 스크립트 생성
RUN echo '#!/bin/bash\nset -e\necho "🔨 커널 빌드 시작..."\ncd /rpi-boot/linux\nmake ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- bcm2711_defconfig\necho "# Disable Broadcom WiFi/BT" >> .config\necho "# CONFIG_BRCMFMAC is not set" >> .config\necho "# CONFIG_BRCMUTIL is not set" >> .config\necho "# CONFIG_BT_HCIUART_BCM is not set" >> .config\necho "# CONFIG_BT_BCM is not set" >> .config\necho "# Enable networking features" >> .config\necho "CONFIG_NETFILTER=y" >> .config\necho "CONFIG_NF_TABLES=y" >> .config\necho "CONFIG_NETFILTER_XTABLES=y" >> .config\necho "CONFIG_NETFILTER_NETLINK=y" >> .config\necho "CONFIG_NL80211_TESTMODE=y" >> .config\necho "CONFIG_CFG80211=y" >> .config\necho "CONFIG_CFG80211_DEBUGFS=y" >> .config\necho "CONFIG_MAC80211=y" >> .config\necho "CONFIG_MAC80211_DEBUGFS=y" >> .config\necho "CONFIG_BRIDGE=y" >> .config\necho "CONFIG_VLAN_8021Q=y" >> .config\necho "⏱️ 커널 컴파일 시작 (예상 시간: 20-30분)"\nmake ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) Image modules dtbs\necho "✅ 커널 빌드 완료"' > /rpi-boot/build_kernel.sh && chmod +x /rpi-boot/build_kernel.sh

RUN echo '#!/bin/bash\nset -e\necho "🔨 루트파일시스템 빌드 시작..."\ncd /rpi-boot/buildroot\necho "pi -1 pi -1 =raspberry /home/pi /bin/bash sudo" > board/users_table.txt\nmake raspberrypi4_64_defconfig\nsed -i "s/BR2_TARGET_ROOTFS_EXT2=y/BR2_TARGET_ROOTFS_EXT2=y\\nBR2_TARGET_ROOTFS_EXT2_4=y/" .config\nsed -i "s/BR2_TARGET_ROOTFS_EXT2_SIZE=\"60M\"/BR2_TARGET_ROOTFS_EXT2_SIZE=\"512M\"/" .config\necho "BR2_PACKAGE_NCURSES=y" >> .config\necho "BR2_PACKAGE_READLINE=y" >> .config\necho "BR2_PACKAGE_OPENSSL=y" >> .config\necho "BR2_PACKAGE_ZLIB=y" >> .config\necho "BR2_PACKAGE_LIBCRYPT=y" >> .config\necho "BR2_PACKAGE_OPENSSH=y" >> .config\necho "BR2_PACKAGE_NANO=y" >> .config\necho "BR2_PACKAGE_VIM=y" >> .config\necho "BR2_PACKAGE_HTOP=y" >> .config\necho "BR2_PACKAGE_BASH=y" >> .config\necho "BR2_PACKAGE_SUDO=y" >> .config\necho "BR2_PACKAGE_UTIL_LINUX=y" >> .config\necho "BR2_PACKAGE_IPTABLES=y" >> .config\necho "BR2_PACKAGE_IPROUTE2=y" >> .config\necho "BR2_PACKAGE_NET_TOOLS=y" >> .config\necho "BR2_PACKAGE_DHCP=y" >> .config\necho "BR2_PACKAGE_DHCPCD=y" >> .config\necho "BR2_PACKAGE_HOSTAPD=y" >> .config\necho "BR2_PACKAGE_WPA_SUPPLICANT=y" >> .config\necho "BR2_PACKAGE_WPA_SUPPLICANT_NL80211=y" >> .config\necho "BR2_PACKAGE_WIRELESS_TOOLS=y" >> .config\necho "BR2_PACKAGE_IW=y" >> .config\necho "BR2_PACKAGE_LIBNL=y" >> .config\necho "BR2_PACKAGE_BRIDGE_UTILS=y" >> .config\necho "BR2_SYSTEM_DEFAULT_PATH=\"/bin:/sbin:/usr/bin:/usr/sbin\"" >> .config\necho "BR2_SYSTEM_ROOT_PASSWORD=\"raspberry\"" >> .config\necho "BR2_SYSTEM_ENABLE_NLS=y" >> .config\necho "BR2_ROOTFS_USERS_TABLES=\"board/users_table.txt\"" >> .config\necho "⏱️ Buildroot 컴파일 시작 (예상 시간: 10-15분)"\nmake -j$(nproc)\necho "✅ 루트파일시스템 빌드 완료"' > /rpi-boot/build_rootfs.sh && chmod +x /rpi-boot/build_rootfs.sh

RUN echo '#!/bin/bash\nset -e\necho "🔨 최종 부팅 이미지 생성..."\ncd /rpi-boot\nmkdir -p image/boot\ncp firmware/boot/start*.elf image/boot/\ncp firmware/boot/fixup*.dat image/boot/\ncp linux/arch/arm64/boot/Image image/boot/kernel8.img\ncp linux/arch/arm64/boot/dts/broadcom/bcm2711*.dtb image/boot/\nmkdir -p image/boot/overlays\ncp linux/arch/arm64/boot/dts/overlays/*.dtbo image/boot/overlays/ || true\ncat > image/boot/config.txt << EOF\narm_64bit=1\nkernel=kernel8.img\ndevice_tree_address=0x03000000\ndtoverlay=vc4-kms-v3d\nmax_framebuffers=2\ngpu_mem=128\nenable_uart=1\nEOF\ndd if=/dev/zero of=rpi4-complete.img bs=1M count=2048\nparted rpi4-complete.img --script mklabel msdos\nparted rpi4-complete.img --script mkpart primary fat32 1MiB 257MiB\nparted rpi4-complete.img --script mkpart primary ext4 257MiB 100%\nparted rpi4-complete.img --script set 1 boot on\nLOOP_DEV=$(losetup -f)\nlosetup $LOOP_DEV rpi4-complete.img\npartprobe $LOOP_DEV\nmkfs.vfat -F32 ${LOOP_DEV}p1\nmkfs.ext4 ${LOOP_DEV}p2\nmkdir -p /tmp/boot_mount /tmp/root_mount\nmount ${LOOP_DEV}p1 /tmp/boot_mount\ncp -r image/boot/* /tmp/boot_mount/\nROOT_PARTUUID=$(blkid ${LOOP_DEV}p2 -s PARTUUID -o value)\necho "console=serial0,115200 console=tty1 root=PARTUUID=$ROOT_PARTUUID rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait" > /tmp/boot_mount/cmdline.txt\numount /tmp/boot_mount\nmount ${LOOP_DEV}p2 /tmp/root_mount\ntar -xf buildroot/output/images/rootfs.tar -C /tmp/root_mount/\ncd linux && make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- INSTALL_MOD_PATH=/tmp/root_mount modules_install && cd ..\numount /tmp/root_mount\nlosetup -d $LOOP_DEV\necho "🎉 RPi4 완전한 부팅 이미지 생성 완료!"\nls -lh rpi4-complete.img' > /rpi-boot/create_image.sh && chmod +x /rpi-boot/create_image.sh

# 전체 빌드 실행 스크립트
RUN echo '#!/bin/bash\nset -e\necho "🚀 RPi4 부팅 이미지 전체 빌드 시작"\necho "📅 $(date)"\n/rpi-boot/build_kernel.sh\n/rpi-boot/build_rootfs.sh\n/rpi-boot/create_image.sh\necho "🎉 모든 빌드 완료!"' > /rpi-boot/build_all.sh && chmod +x /rpi-boot/build_all.sh

CMD ["/bin/bash"]