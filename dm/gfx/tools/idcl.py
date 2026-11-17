"""Bounded reader for Switch id Tech 6 IDCL v12 rendering resources.

The directory's name field indexes *u64 words* in the reference table, rather
than the PC reader's sequential pair per entry. Verified on Wolfenstein II 1.2.
Only renderProgResource payloads are decoded, with the game's own Oodle.
"""
import struct
from romfs import open


def shader_members(path, decode):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        length = f.tell()

        def read(at, size):
            if at < 0 or size < 0 or at > length or size > length - at:
                raise ValueError(f'{path}: IDCL range {at:#x}+{size:#x} exceeds archive')
            f.seek(at)
            data = f.read(size)
            if len(data) != size:
                raise ValueError(f'{path}: truncated IDCL range')
            return data

        h = read(0, 120)
        if h[:8] != b'IDCL\x0c\0\0\0':
            raise ValueError(f'{path}: unsupported IDCL header/version')
        count, ids = (struct.unpack_from('<I', h, at)[0] for at in (40, 48))
        strings, strings_end, directory, refs, data = (struct.unpack_from('<Q', h, at)[0] for at in (72, 80, 88, 104, 112))
        # Empty patch sound packs end at their tables; the aligned first-data
        # offset is beyond EOF because there is no payload to align.
        if count == 0 and 120 <= directory <= strings < strings_end <= refs <= length:
            return
        if not (120 <= directory <= strings < strings_end <= refs <= data <= length):
            raise ValueError(f'{path}: invalid IDCL table order')
        if count > (strings - directory) // 144 or strings_end - strings > 128 << 20:
            raise ValueError(f'{path}: invalid IDCL directory/string table size')
        table = read(directory, count * 144)
        text = read(strings, strings_end - strings)
        if len(text) < 8:
            raise ValueError(f'{path}: truncated IDCL string table')
        ns = struct.unpack_from('<Q', text)[0]
        if ns > (len(text) - 8) // 8:
            raise ValueError(f'{path}: invalid IDCL string count')
        start = 8 + ns * 8

        def name(index):
            if index >= ns:
                raise ValueError(f'{path}: invalid IDCL string index')
            at = start + struct.unpack_from('<Q', text, 8 + index * 8)[0]
            end = text.find(b'\0', at)
            if at >= len(text) or end < 0:
                raise ValueError(f'{path}: unterminated IDCL string')
            return text[at:end].decode('utf-8')

        ref_start = refs + ids * 4
        if ref_start > data or data - ref_start > 64 << 20:
            raise ValueError(f'{path}: invalid IDCL reference table size')
        references = read(ref_start, data - ref_start)
        for i in range(count):
            at = i * 144
            index = struct.unpack_from('<Q', table, at + 32)[0]
            if index > len(references) // 8 - 2:
                raise ValueError(f'{path}: invalid IDCL resource reference')
            kind, nm = struct.unpack_from('<QQ', references, index * 8)
            if name(kind) != 'renderProgResource':
                continue
            nm = name(nm)
            offset, packed, size = struct.unpack_from('<QQQ', table, at + 56)
            if offset < data or not 0 < packed <= 64 << 20 or not 0 < size <= 64 << 20:
                raise ValueError(f'{path}#{nm}: invalid IDCL rendering resource range')
            raw = read(offset, packed)
            if packed != size:
                if raw[:1] != b'\x8c':
                    raise ValueError(f'{path}#{nm}: unsupported IDCL rendering resource compression')
                raw = decode(raw, size)
            if len(raw) != size:
                raise ValueError(f'{path}#{nm}: wrong decoded IDCL rendering resource size')
            yield nm, raw
