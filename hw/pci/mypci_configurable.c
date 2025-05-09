#include "qemu/osdep.h"
#include "qemu/module.h"
#include "hw/pci/pci.h"
#include "hw/pci/pci_ids.h"
#include "hw/pci/pci_device.h"
#include "hw/pci/pci_bus.h"
#include "hw/qdev-properties.h"
#include "qapi/error.h"

typedef struct MyPCIConfigurableDevice {
    PCIDevice parent_obj;
    MemoryRegion mmio;
    uint32_t reg;
} MyPCIConfigurableDevice;

static uint64_t mypci_configurable_mmio_read(void *opaque, hwaddr addr, unsigned size) {
    MyPCIConfigurableDevice *d = opaque;
    printf("[mypci_configurable] MMIO READ: addr=0x%lx size=%u -> value=0x%x\n",
           (unsigned long)addr, size, d->reg);
    fflush(stdout);
    return d->reg;
}

static void mypci_configurable_mmio_write(void *opaque, hwaddr addr, uint64_t val, unsigned size) {
    MyPCIConfigurableDevice *d = opaque;
    d->reg = val;
    printf("[mypci_configurable] MMIO WRITE: addr=0x%lx size=%u val=0x%lx\n",
           (unsigned long)addr, size, (unsigned long)val);
    fflush(stdout);
}

/////////////////////////////////////////

static const MemoryRegionOps mypci_configurable_mmio_ops = {
    .read = mypci_configurable_mmio_read,
    .write = mypci_configurable_mmio_write,
    .endianness = DEVICE_NATIVE_ENDIAN,
};

static void mypci_configurable_realize(PCIDevice *pdev, Error **errp) {
    MyPCIConfigurableDevice *d = DO_UPCAST(MyPCIConfigurableDevice, parent_obj, pdev);
    memory_region_init_io(&d->mmio, OBJECT(d), &mypci_configurable_mmio_ops, d, "mypci_configurable-mmio", 0x1000);
    pci_register_bar(pdev, 0, PCI_BASE_ADDRESS_SPACE_MEMORY, &d->mmio);
}

static const Property mypci_configurable_properties[] = {
    DEFINE_PROP_UINT32("reg", MyPCIConfigurableDevice, reg, 0),
};

static void mypci_configurable_class_init(ObjectClass *klass, void *data) {
    PCIDeviceClass *k = PCI_DEVICE_CLASS(klass);
    k->realize    = mypci_configurable_realize;
    k->vendor_id  = PCI_VENDOR_ID_REDHAT_QUMRANET;
    k->device_id  = 0x1234;
    k->revision   = 0x01;
    k->class_id   = PCI_CLASS_OTHERS;

    DeviceClass *dc = DEVICE_CLASS(klass);
    device_class_set_props(dc, mypci_configurable_properties);
}


static const TypeInfo mypci_configurable_info = {
    .name          = "mypci_configurable",
    .parent        = TYPE_PCI_DEVICE,
    .instance_size = sizeof(MyPCIConfigurableDevice),
    .class_init    = mypci_configurable_class_init,
    .interfaces    = (InterfaceInfo[]) {
         { INTERFACE_CONVENTIONAL_PCI_DEVICE },
         { },
    },
};

static void mypci_configurable_register_types(void) {
    type_register_static(&mypci_configurable_info);
}

type_init(mypci_configurable_register_types)
