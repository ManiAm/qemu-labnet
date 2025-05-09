
## mypci_minimal

The [mypci_minimal.c](hw/pci/mypci_minimal.c) module defines a minimal conventional PCI device in QEMU. It registers a memory-mapped I/O (MMIO) region, exposes a single 32-bit register (reg), and enables basic read/write interaction between the guest operating system and the emulated device.

**Device Registration and Initialization Flow**

`mypci_minimal_register_types()` is invoked automatically at QEMU startup via the `type_init()` macro. It registers the new device type (`mypci_minimal`) and associates it with metadata defined in the `mypci_minimal_info` structure. This makes the device discoverable by QEMU's object model and usable via the `-device` CLI option.

`mypci_minimal_class_init()` is called once during type registration. It initializes class-level properties of the PCI device, including key identifiers and behavior. These fields are essential for integration into QEMU’s PCI subsystem and for guest-side enumeration:

| Field       | Description                                                                          |
|-------------|--------------------------------------------------------------------------------------|
| `realize`   | The realize callback. Called when the device is fully instantiated.                  |
| `vendor_id` | PCI Vendor ID. Identifies the manufacturer.                                          |
| `device_id` | Device ID assigned by the vendor. Identifies the specific model.                     |
| `revision`  | Device revision number. Often used by drivers to detect features or hardware errata. |
| `class_id`  | Defines the PCI [class code](https://github.com/qemu/qemu/blob/master/include/hw/pci/pci_ids.h) (storage, network, display, bridge, serial, memory, etc).   |

The combination of vendor_id and device_id is commonly referred to as the PCI ID and is used by the guest OS (e.g., via lspci) to identify and match drivers to the device.

`mypci_minimal_realize()` is called when the device is instantiated during QEMU's runtime (i.e., when `-device mypci_minimal` is parsed). This function sets up the internal memory region using `memory_region_init_io()` and registers a BAR 0 using `pci_register_bar()`. A BAR (Base Address Register) is a standard PCI mechanism for defining the physical address space a device will respond to, either via MMIO or I/O ports. If realization fails, the device will not be visible to the guest.

**Guest Interaction**

Once the device is instantiated and running, the guest OS can read from and write to the mapped MMIO BAR. These accesses are handled by the device’s I/O callbacks:

- `mypci_minimal_mmio_read()` — triggered on guest read operations.
- `mypci_minimal_mmio_write()` — triggered on guest write operations.

Both functions directly operate on the internal reg field, enabling simple state inspection and manipulation by the guest software. This emulates basic device interaction and can be extended with additional registers, interrupts, or DMA support as needed.

**Run a QEMU VM with mypci_minimal**

We can now run QEMU with mypci_minimal using the `-device` option:

    -device mypci_minimal

Connect to the Alpine Linux VM by:

```bash
/workspace# telnet 127.0.0.1 4567
```

And then install pciutils package:

```bash
apk add pciutils
```

Our custom mypci_minimal is successfully detected inside the VM:

```bash
lspci

00:00.0 Host bridge: Red Hat, Inc. QEMU PCIe Host bridge
00:01.0 Unclassified device [00ff]: Red Hat, Inc. Device 1234 (rev 01)  <-------
00:02.0 Ethernet controller: Intel Corporation 82540EM Gigabit Ethernet Controller (rev 03)
00:03.0 Ethernet controller: Intel Corporation 82540EM Gigabit Ethernet Controller (rev 03)
00:04.0 Unclassified device [0002]: Red Hat, Inc. Virtio filesystem
00:05.0 SCSI storage controller: Red Hat, Inc. Virtio block device
```

**PCI Configuration Space**

The PCI configuration space is a standardized 256-byte memory area used by the operating system and firmware to identify and configure PCI devices. It contains critical fields such as the vendor ID, device ID, class code, command/status registers, and base address registers (BARs) that define how the device interacts with the system—particularly how memory or I/O space is mapped. This space also includes optional fields for interrupt configuration, capabilities like MSI, and subsystem identifiers.

When developing or debugging PCI devices (such as with QEMU), inspecting this space via tools like `lspci` helps verify that the device is properly registered, configured, and exposing its resources as intended. To dump the raw PCI config space for our device:

```bash
lspci -s 00:01.0 -xxxx

00:01.0 Unclassified device [00ff]: Red Hat, Inc. Device 1234 (rev 01)
00: f4 1a 34 12 02 00 00 00 01 00 ff 00 00 00 00 00
10: 00 00 0c 10 00 00 00 00 00 00 00 00 00 00 00 00
20: 00 00 00 00 00 00 00 00 00 00 00 00 f4 1a 00 11
30: 00 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00
40: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
50: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
60: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
70: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
90: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
a0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
b0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
c0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
d0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
e0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
f0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

To read the same PCI config space, but instead of hex dump, show a human-readable, decoded interpretation:

```bash
lspci -s 00:01.0 -vvv

00:01.0 Unclassified device [00ff]: Red Hat, Inc. Device 1234 (rev 01)
        Subsystem: Red Hat, Inc. Device 1100
        Control: I/O- Mem+ BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
        Status: Cap- 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
        Region 0: Memory at 100c0000 (32-bit, non-prefetchable) [size=4K]
```

`Mem+` means the device has a memory BAR mapped and enabled. `I/O-` and `BusMaster-` mean it does not have I/O space access or DMA (bus mastering). Other flags are disabled — typical for minimal devices.

The device has one MMIO region, mapped to 0x100c0000 in guest physical memory. Size is 4 KB, which matches our `memory_region_init_io()` call in QEMU. This region is where reads/writes from the guest OS will go, triggering our `mypci_minimal_mmio_read/write` callbacks.

`setpci` is a powerful utility used to read from and write to the PCI configuration space of devices, allowing direct manipulation of specific registers at defined offsets. Unlike `lspci`, which is primarily for inspection, `setpci` can modify settings, making it useful for low-level debugging, testing, or reconfiguring device behavior. For example, to get the vendor_id:

```bash
setpci -s 00:01.0 00.w

1af4
```

**Read from and Write to MMIO memory**

`mmio_rw.py` is a lightweight utility for reading from and writing to physical memory-mapped I/O (MMIO) regions on Linux systems using /dev/mem, which exposes physical memory to user space. This tool is especially useful in embedded systems, hardware development, or virtual environments like QEMU, where users need to interact directly with custom hardware registers without a device driver.

It accepts an address, read/write mode, and access width (8, 16, 32, or 64 bits), and performs the memory access using mmap and Python’s struct module. This allows developers to verify device behavior, debug register interactions, and test QEMU-emulated hardware directly from a guest OS.

Create a Python virtual environment inside the Alpine VM:

```bash
echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories
apk update
apk add python3 py3-virtualenv py3-pip
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate
```

To read a single 8-bit value from the physical memory address `0x100c0000`:

```bash
python3 ./mmio_rw.py 0x100c0000 r 8
```

The value `0x100c0000` is the physical memory address of our custom PCI device’s BAR0 (Base Address Register 0), as reported by `lspci`. This will trigger our QEMU device's `.read` callback for MMIO and helps us inspect the register value. Open the `qemu.log` to check the log:

```text
[mypci_minimal] MMIO READ: addr=0x0 size=1 -> value=0x0
```

## mypci_configurable

QEMU’s device model provides a flexible mechanism for defining configurable properties on devices. These properties are exposed via the `-device` command-line option and allow users to customize the behavior or initial state of a device at VM startup—without modifying guest software or the device model itself.

The [mypci_configurable.c](hw/pci/mypci_configurable.c) module defines a conventional PCI device that includes a configurable 32-bit register named `reg`. This property is declared using QEMU’s `DEFINE_PROP_UINT32` macro, which makes it accessible at runtime via the command line. For example, the following option:

    -device mypci_configurable,reg=0x42

Instantiates the mypci_configurable PCI device and sets its `reg` field to `0x42` before the guest boots. This value becomes the initial contents of the device’s MMIO register, which can then be read by the guest operating system through memory-mapped I/O. Such configuration is particularly useful for testing, feature toggling, or emulating specific device states in virtual environments.

## More Advanced


expand this with:
PCIe capability
add interrupt support (INTx/MSI)
implement custom configuration space behavior


Optionally enhance the device by adding:

A second BAR
Interrupt support (MSI or legacy)
Bus mastering (DMA) capability

call-backs outside of QEMU source code
