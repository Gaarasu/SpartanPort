#!/usr/bin/env python3
"""Wrap the PS4 ELF written by scripts/prepare.py in a minimal PE32+ so REA's Windows Ghidra can open it.

REA's Windows Ghidra provider accepts only PE files, and Ghidra has no loader for the PS4 ELF type
(0xfe10). The wrapper maps every PT_LOAD of the ELF as a PE section so that, in Ghidra, an address is
the PS4 virtual address: ImageBase + section RVA = PS4 image base (0x400000) + image offset.

  python .claude/tools/mkpe.py out/eboot.elf OUT.exe [--ps4-base 0x400000] [--shift 0x10000]
  python .claude/tools/mkpe.py --self-test

Open the result with REA: open_binary path=<OUT.exe> provider_id=ghidra (no format or architecture).
Analysis is static only; the PE is never meant to run. Its entry point is the ELF's e_entry (an image
offset for these files), i.e. PS4 vaddr 0x400000 + e_entry.

The output contains game code. Write it outside the repository (a temp or scratch folder); the script
refuses a path inside the repo unless it is under out/, which is gitignored. Never commit it.
"""
import argparse
import struct
from pathlib import Path

ET_MACHINE_X86_64 = 0x3E
PT_LOAD, PF_X, PF_W = 1, 1, 2
FILE_ALIGN, SECTION_ALIGN = 0x200, 0x1000
OPTIONAL_HEADER_SIZE = 240
# Section characteristics: code | execute | read, and initialized data | read | write.
CODE_FLAGS, DATA_FLAGS = 0x60000020, 0xC0000040
ROOT = Path(__file__).resolve().parent.parent.parent


def align(value, boundary):
    return (value + boundary - 1) // boundary * boundary


def read_segments(elf):
    """(entry, [(flags, vaddr, filesz, memsz, data)]) for the PT_LOAD headers of an ELF64 x86-64 file."""
    if elf[:4] != b'\x7fELF' or elf[4] != 2:
        raise ValueError('not an ELF64 file')
    machine, = struct.unpack_from('<H', elf, 0x12)
    if machine != ET_MACHINE_X86_64:
        raise ValueError(f'ELF machine 0x{machine:x} is not x86-64')
    entry, phoff = struct.unpack_from('<QQ', elf, 0x18)
    phentsize, phnum = struct.unpack_from('<HH', elf, 0x36)
    segments = []
    for index in range(phnum):
        ptype, flags, offset, vaddr, _paddr, filesz, memsz, _palign = struct.unpack_from(
            '<IIQQQQQQ', elf, phoff + index * phentsize)
        if ptype != PT_LOAD or memsz == 0:
            continue
        if offset + filesz > len(elf):
            raise ValueError(f'PT_LOAD {index} runs past the end of the file')
        segments.append((flags, vaddr, filesz, memsz, elf[offset:offset + filesz]))
    if not segments:
        raise ValueError('no PT_LOAD segments')
    return entry, sorted(segments, key=lambda s: s[1])


def build_pe(elf, ps4_base=0x400000, shift=0x10000):
    """The PE bytes for the ELF. Section RVA = segment vaddr + shift, ImageBase = ps4_base - shift."""
    image_base = ps4_base - shift
    if image_base <= 0 or image_base % 0x10000 or shift % SECTION_ALIGN or shift < 0x1000:
        raise ValueError('ps4-base minus shift must be a positive multiple of 0x10000; shift a multiple of 0x1000')
    entry, segments = read_segments(elf)
    previous_end = 0
    sections = []
    counts = {'.text': 0, '.data': 0}
    for flags, vaddr, filesz, memsz, data in segments:
        if vaddr % SECTION_ALIGN:
            raise ValueError(f'segment vaddr 0x{vaddr:x} is not page aligned')
        if vaddr < previous_end:
            raise ValueError(f'segment at 0x{vaddr:x} overlaps the previous one')
        previous_end = vaddr + memsz
        kind = '.text' if flags & PF_X else '.data'
        counts[kind] += 1
        name = kind if counts[kind] == 1 else f'{kind}{counts[kind] - 1}'
        sections.append((name.encode(), vaddr + shift, memsz, data, CODE_FLAGS if flags & PF_X else DATA_FLAGS))
    if not any(vaddr <= entry < vaddr + memsz and flags & PF_X for flags, vaddr, _f, memsz, _d in segments):
        raise ValueError(f'entry 0x{entry:x} is not inside an executable segment')

    header_size = align(0x40 + 4 + 20 + OPTIONAL_HEADER_SIZE + 40 * len(sections), FILE_ALIGN)
    size_of_image = align(max(rva + size for _n, rva, size, _d, _c in sections), SECTION_ALIGN)
    code = sum(len(d) for n, _r, _s, d, c in sections if c == CODE_FLAGS)
    init = sum(len(d) for n, _r, _s, d, c in sections if c == DATA_FLAGS)

    dos = b'MZ' + b'\0' * 0x3A + struct.pack('<I', 0x40)
    coff = struct.pack('<HHIIIHH', 0x8664, len(sections), 0, 0, 0, OPTIONAL_HEADER_SIZE, 0x0022)
    optional = struct.pack('<HBBIIIII', 0x20B, 14, 0, code, init, 0, shift + entry, shift)
    optional += struct.pack('<QIIHHHHHHIIIIHHQQQQII', image_base, SECTION_ALIGN, FILE_ALIGN, 6, 0, 0, 0, 6, 0, 0,
                            size_of_image, header_size, 0, 3, 0x8000, 0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    optional += b'\0' * (16 * 8)
    table, body, pointer = b'', b'', header_size
    for name, rva, size, data, flags in sections:
        raw_size = align(len(data), FILE_ALIGN)
        table += struct.pack('<8sIIIIIIHHI', name, size, rva, raw_size, pointer if raw_size else 0, 0, 0, 0, 0, flags)
        body += data + b'\0' * (raw_size - len(data))
        pointer += raw_size
    headers = dos + b'PE\0\0' + coff + optional + table
    return headers + b'\0' * (header_size - len(headers)) + body


def verify(pe, elf, ps4_base, shift):
    """Parse the PE back with struct and check each section against the ELF. Raises AssertionError."""
    entry, segments = read_segments(elf)
    assert pe[:2] == b'MZ'
    pe_offset, = struct.unpack_from('<I', pe, 0x3C)
    assert pe[pe_offset:pe_offset + 4] == b'PE\0\0'
    _machine, count = struct.unpack_from('<HH', pe, pe_offset + 4)
    optional = pe_offset + 24
    assert struct.unpack_from('<H', pe, optional)[0] == 0x20B
    assert struct.unpack_from('<I', pe, optional + 16)[0] == shift + entry, 'entry point'
    assert struct.unpack_from('<Q', pe, optional + 24)[0] == ps4_base - shift, 'image base'
    table = optional + OPTIONAL_HEADER_SIZE
    assert count == len(segments)
    for index, (_flags, vaddr, filesz, memsz, data) in enumerate(segments):
        _n, vsize, rva, raw_size, pointer = struct.unpack_from('<8sIIII', pe, table + 40 * index)
        assert (vsize, rva) == (memsz, vaddr + shift), f'section {index} layout'
        assert pe[pointer:pointer + filesz] == data, f'section {index} bytes'
        assert ps4_base - shift + rva == ps4_base + vaddr, 'address mapping'


def self_test():
    """Synthetic ELF (no game data): text with an entry, data with a bss tail. No arguments, exits 0 on success."""
    text, data = bytes(range(256)) * 16, b'\xaa' * 64
    ph = [struct.pack('<IIQQQQQQ', PT_LOAD, 5, 0x1000, 0, 0, len(text), len(text), 0x1000),
          struct.pack('<IIQQQQQQ', PT_LOAD, 6, 0x1000 + len(text), 0x2000, 0, len(data), 0x8000, 0x1000),
          struct.pack('<IIQQQQQQ', 2, 6, 0, 0, 0, 0, 0, 8)]  # not a PT_LOAD: ignored
    header = bytearray(0x40)
    header[:5] = b'\x7fELF\x02'
    struct.pack_into('<H', header, 0x12, ET_MACHINE_X86_64)
    struct.pack_into('<QQ', header, 0x18, 0x40, 0x40)  # entry inside the text, phoff
    struct.pack_into('<HH', header, 0x36, 56, len(ph))
    elf = bytes(header) + b''.join(ph)
    elf += b'\0' * (0x1000 - len(elf)) + text + data
    pe = build_pe(elf)
    verify(pe, elf, 0x400000, 0x10000)
    verify(build_pe(elf, 0x140001000, 0x1000), elf, 0x140001000, 0x1000)
    try:
        build_pe(elf, 0x140000000, 0x1000)  # ImageBase 0x13ffff000 is not 64 KiB aligned
    except ValueError:
        pass
    else:
        raise AssertionError('an unaligned ImageBase was accepted')
    for bad in (b'', b'\x7fELF\x01' + b'\0' * 60, elf[:0x1100]):
        try:
            build_pe(bad)
        except (ValueError, struct.error):
            continue
        raise AssertionError('a malformed ELF was accepted')
    try:
        import pefile
    except ImportError:
        note = 'pefile not installed, struct check only'
    else:
        parsed = pefile.PE(data=pe)
        assert parsed.OPTIONAL_HEADER.ImageBase == 0x3F0000 and len(parsed.sections) == 2
        note = 'pefile agrees'
    print(f'mkpe self-test: OK ({note})')


def check_destination(path):
    resolved = path.resolve()
    try:
        inside = resolved.relative_to(ROOT)
    except ValueError:
        return
    if inside.parts and inside.parts[0] != 'out':
        raise SystemExit(f'Refusing to write game-derived output inside the repo ({inside}). Use a temp or scratch folder.')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('elf', nargs='?', type=Path, help='ELF from scripts/prepare.py (out/eboot.elf)')
    parser.add_argument('output', nargs='?', type=Path, help='PE to write, outside the repo')
    parser.add_argument('--ps4-base', type=lambda v: int(v, 0), default=0x400000)
    parser.add_argument('--shift', type=lambda v: int(v, 0), default=0x10000)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.elf or not args.output:
        parser.error('give the ELF and the output path, or --self-test')
    check_destination(args.output)
    elf = args.elf.read_bytes()
    pe = build_pe(elf, args.ps4_base, args.shift)
    verify(pe, elf, args.ps4_base, args.shift)
    args.output.write_bytes(pe)
    entry, _segments = read_segments(elf)
    print(f'wrote {args.output} ({len(pe)} bytes); ImageBase 0x{args.ps4_base - args.shift:x}, '
          f'entry at PS4 vaddr 0x{args.ps4_base + entry:x}')


if __name__ == '__main__':
    main()
