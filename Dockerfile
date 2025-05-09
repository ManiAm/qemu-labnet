FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH

# Install all required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ninja-build git python3 python3-venv python3-pip \
    python3-sphinx libglib2.0-dev libfdt-dev libpixman-1-dev zlib1g-dev \
    libaio-dev libcap-ng-dev libattr1-dev libepoxy-dev \
    libusb-1.0-0-dev libsnappy-dev libcurl4-openssl-dev \
    libseccomp-dev pkg-config ca-certificates cpu-checker \
    wget curl nano file iputils-ping net-tools iproute2 bridge-utils tcpdump \
    cpio unzip telnet htop rsync bc libncurses5-dev libssl-dev flex bison libelf-dev \
    libslirp-dev m4 gperf qemu-efi-aarch64

# Build and install Nettle from source (required for QEMU --enable-nettle)
WORKDIR /tmp
RUN wget https://ftp.gnu.org/gnu/nettle/nettle-3.10.tar.gz && \
    tar xf nettle-3.10.tar.gz && \
    cd nettle-3.10 && \
    ./configure --prefix=/usr/local && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf nettle-3.10*

# Ensure both pkg-config and dynamic linker can find the right libraries
ENV PKG_CONFIG_PATH=/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig
ENV LD_LIBRARY_PATH=/usr/local/lib64:/usr/local/lib

WORKDIR /opt

RUN git clone https://gitlab.com/qemu-project/qemu.git && \
    cd qemu && \
    git checkout v10.0.0

RUN python3 -m venv qemu-venv && \
    qemu-venv/bin/pip install --upgrade pip tomli meson ninja flask flask-restx

##### Custom PCI Devices #####

# Copy into the source tree
COPY hw/pci/mypci_minimal.c /opt/qemu/hw/pci/
COPY hw/pci/mypci_configurable.c /opt/qemu/hw/pci/

# Patch meson.build to include our PCI device
RUN sed -i '/system_ss\.add_all.*pci_ss/i \pci_ss.add(files('"'"'mypci_minimal.c'"'"'))' /opt/qemu/hw/pci/meson.build
RUN sed -i '/system_ss\.add_all.*pci_ss/i \pci_ss.add(files('"'"'mypci_configurable.c'"'"'))' /opt/qemu/hw/pci/meson.build

############################

RUN if [ "$TARGETARCH" = "amd64" ]; then \
        export QEMU_TARGET="x86_64-softmmu"; \
    else \
        export QEMU_TARGET="aarch64-softmmu"; \
    fi && \
    echo "Using QEMU target: $QEMU_TARGET" && \
    cd /opt/qemu && \
    . /opt/qemu-venv/bin/activate && \
    ./configure \
        --target-list=$QEMU_TARGET \
        --enable-kvm \
        --enable-user \
        --enable-nettle \
        --enable-slirp && \
    make -j$(nproc) && \
    make install

WORKDIR /workspace

RUN if [ "$TARGETARCH" = "arm64" ]; then \
      echo "Downloading Alpine AARCH64 ISO..."; \
      wget -O alpine.iso https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/aarch64/alpine-virt-3.21.3-aarch64.iso; \
    else \
      echo "Downloading Alpine x86_64 ISO..."; \
      wget -O alpine.iso https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/x86_64/alpine-virt-3.21.3-x86_64.iso; \
    fi

COPY app.py .
COPY qmp_client.py .
COPY templates/ templates/
COPY static/ static/

COPY setup_vm_network.sh .
RUN chmod +x setup_vm_network.sh

COPY mmio_rw.py .
RUN chmod +x mmio_rw.py

CMD ["/bin/bash"]
