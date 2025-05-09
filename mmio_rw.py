#!/usr/bin/env python3

# Author: Mani Amoozadeh
# Email: mani.amoozadeh2@gmail.com

import mmap
import struct
import sys

PAGE_SIZE = mmap.PAGESIZE
PAGE_MASK = ~(PAGE_SIZE - 1)

formats = {
    8:  ("<B", 1),
    16: ("<H", 2),
    32: ("<I", 4),
    64: ("<Q", 8),
}

def usage():
    print(f"Usage: {sys.argv[0]} <address> <r|w> <width> [value]")
    print("  address : physical address (e.g., 0x100c0000)")
    print("  r|w     : read or write")
    print("  width   : 8, 16, 32, or 64 (bits)")
    print("  value   : value to write (only for 'w')")
    print("Examples:")
    print(f"  {sys.argv[0]} 0x100c0000 r 32")
    print(f"  {sys.argv[0]} 0x100c0000 w 32 0xdeadbeef")
    sys.exit(1)

if len(sys.argv) < 4:
    usage()

addr = int(sys.argv[1], 0)
mode = sys.argv[2].lower()
width = int(sys.argv[3])
is_write = mode == 'w'

if width not in formats:
    print("Unsupported width. Use 8, 16, 32, or 64.")
    usage()

fmt, size = formats[width]

if is_write:
    if len(sys.argv) < 5:
        print("Missing value for write.")
        usage()
    value = int(sys.argv[4], 0)

base = addr & PAGE_MASK
offset = addr - base

with open("/dev/mem", "r+b") as f:
    mm = mmap.mmap(f.fileno(), PAGE_SIZE, offset=base)

    if is_write:
        mm.seek(offset)
        mm.write(struct.pack(fmt, value))
        print(f"Wrote 0x{value:0{width // 4}x} to 0x{addr:08x} ({width} bits)")
    else:
        mm.seek(offset)
        data = mm.read(size)
        val = struct.unpack(fmt, data)[0]
        print(f"Read  0x{val:0{width // 4}x} from 0x{addr:08x} ({width} bits)")

    mm.close()
