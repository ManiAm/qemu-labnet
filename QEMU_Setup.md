
## Setting up QEMU

Source the environment configuration:

```bash
source docker-env.sh
```

This script automatically detects the host system's architecture and exports the appropriate environment variables. Sourcing this script ensures these variables are available to Docker Compose at runtime.

Build the Docker image:

```bash
docker compose build
```

Start the container in detached mode:

```bash
docker compose up -d
```

The `--device /dev/kvm` option mounts the KVM device from the host into the container, enabling hardware acceleration for virtual machines.

## Start VM on x86_64

Open an interactive shell to the container:

```bash
docker exec -it qemu-x86 bash
```

To verify that KVM is accessible inside the container:

```bash
/workspace# kvm-ok
```

We are going to use qemu-system-x86_64:

```bash
/workspace# qemu-system-x86_64 --version

QEMU emulator version 10.0.0 (v10.0.0-dirty)
Copyright (c) 2003-2025 Fabrice Bellard and the QEMU Project developers
```

Create a 2 GB virtual disk image in qcow2 format. This will act as the VM's hard drive. Note that the qcow2 format allows the file to expand as necessary, so don't be afraid to make the file bigger if you want to.

```bash
/workspace# qemu-img create -f qcow2 alpine_x86.qcow2 2G
```

Start the Alpine VM by:

```bash
/workspace# nohup qemu-system-x86_64 \
    -m 512 \
    -accel kvm \
    -hda alpine_x86.qcow2 \
    -cdrom alpine.iso \
    -boot d \
    -nographic \
    -netdev user,id=net0 -device e1000,netdev=net0 \
    -netdev tap,id=net1tap,ifname=tap1,script=no,downscript=no \
    -device e1000,netdev=net1tap \
    -serial telnet:127.0.0.1:4567,server,nowait > qemu.log 2>&1 &
```

QEMU will allocate 512 MB of RAM to the VM and uses `alpine_x86.qcow2` as the hard disk. The boot option specifies the boot order of devices where each letter represents different types of devices from which the VM can boot. Letter `d` means to boot from the CD-ROM first.

The `-accel` option allows specifying multiple accelerators. To list all the available acceleration, use the following:

```bash
/workspace# qemu-system-x86_64 -accel help

Accelerators supported in QEMU binary:
tcg
kvm
```

QEMU sets up a telnet server on your local machine (127.0.0.1) at port 4567. You can then connect to this server using a telnet client to interact with the serial console of the emulated machine:

```bash
/workspace# telnet 127.0.0.1 4567
```

When the login prompt appears, login as `root`. After a successful login, you will see the shell prompt (`#`). At this point you are running fully operational Linux. To start the installation of Alpine Linux on the hard disk, run the `setup-alpine` script and follow the prompts. When the script is finished, do not reboot the system; instead shut it down by:

```bash
poweroff
```

We can now boot the VM from the disk. Note that letter `c` denotes the first hard disk.

```bash
/workspace# nohup qemu-system-x86_64 \
    -m 512 \
    -accel kvm \
    -hda alpine_x86.qcow2 \
    -boot c \
    -nographic \
    -netdev user,id=net0 -device e1000,netdev=net0 \
    -netdev tap,id=net1tap,ifname=tap1,script=no,downscript=no \
    -device e1000,netdev=net1tap,mac=52:54:00:12:34:58 \
    -fsdev local,id=myfs,path=/workspace,security_model=mapped \
    -device virtio-9p-pci,fsdev=myfs,mount_tag=workspace-shared \
    -serial telnet:127.0.0.1:4567,server,nowait \
    -monitor telnet:127.0.0.1:1234,server,nowait \
    -qmp unix:./qmp-sock,server,nowait > qemu.log 2>&1 &
```

Connect to the VM by:

```bash
/workspace# telnet 127.0.0.1 4567
```

The `-monitor` option is for access the QEMU monitor console via Telnet. Similarly, `-qmp` starts the QEMU Machine Protocol (QMP) server and creates a Unix domain socket. We will get back to these later.

## Start VM on ARM64

Open an interactive shell to the container:

```bash
docker exec -it qemu-arm bash
```

To verify that KVM is accessible inside the container:

```bash
/workspace# kvm-ok
```

We are going to use qemu-system-aarch64:

```bash
/workspace# qemu-system-aarch64 --version

QEMU emulator version 10.0.0 (v10.0.0-dirty)
Copyright (c) 2003-2025 Fabrice Bellard and the QEMU Project developers
```

Create a 2 GB virtual disk image in qcow2 format. This will act as the VM's hard drive. Note that the qcow2 format allows the file to expand as necessary, so don't be afraid to make the file bigger if you want to.

```bash
/workspace# qemu-img create -f qcow2 alpine_arm.qcow2 2G
```

Both X86 and ARM64 VMs need a BIOS or UEFI firmware to be able to boot. In X86 VM, when you specify the `-cdrom` option, QEMU uses its built-in BIOS or UEFI firmware to boot from the CD-ROM or hard disk. In the ARM64 architecture, on the other hand, the UEFI firmware is not included by default in QEMU, so you need to provide it explicitly.

We need to create and prepare a flash image that can be used as a UEFI firmware image in a QEMU VM. You can build UEFI firmware binary yourself. However, Debian provides some pre-packaged UEFI firmware that we can use. Install the following package:

```bash
/workspace# apt install qemu-efi-aarch64
```

This should place a `QEMU_EFI.fd` file in `/usr/share/qemu-efi-aarch64/`.

Start the Alpine VM by the following invocation. Note the `-bios` option.

```bash
/workspace# nohup qemu-system-aarch64 \
    -M virt \
    -cpu host \
    -m 2048 \
    -accel kvm \
    -hda alpine_arm.qcow2 \
    -cdrom alpine.iso \
    -boot d \
    -nographic \
    -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
    -netdev user,id=net0 -device e1000,netdev=net0 \
    -netdev tap,id=net1tap,ifname=tap1,script=no,downscript=no \
    -device e1000,netdev=net1tap \
    -serial telnet:127.0.0.1:4567,server,nowait > qemu.log 2>&1 &
```

Connect to the VM by:

```bash
/workspace# telnet 127.0.0.1 4567
```

Follow the same steps as in x86 section and install Alpine Linux on the hard disk using the `setup-alpine` script. Use the `poweroff` command to shutdown the VM. Boot the VM from the disk with:

```bash
/workspace# nohup qemu-system-aarch64 \
    -M virt \
    -cpu host \
    -m 2048 \
    -accel kvm \
    -hda alpine_arm.qcow2 \
    -boot c \
    -nographic \
    -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
    -netdev user,id=net0 -device e1000,netdev=net0 \
    -netdev tap,id=net1tap,ifname=tap1,script=no,downscript=no \
    -device e1000,netdev=net1tap,mac=52:54:00:12:34:57 \
    -fsdev local,id=myfs,path=/workspace,security_model=mapped \
    -device virtio-9p-pci,fsdev=myfs,mount_tag=workspace-shared \
    -serial telnet:127.0.0.1:4567,server,nowait \
    -monitor telnet:127.0.0.1:1234,server,nowait \
    -qmp unix:./qmp-sock,server,nowait > qemu.log 2>&1 &
```

Connect to the VM by:

```bash
/workspace# telnet 127.0.0.1 4567
```
