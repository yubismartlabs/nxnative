"""Alchemy v12 IGA shader assets: stored/LZMA/mixed blocks and damaged tables.

Synthetic archive bytes only. Run from an NXNative checkout with unittest.
"""
import lzma
import struct
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'dm/tools'))
sys.path.insert(0, str(REPO / 'dm/gfx/tools'))
import alchemy


def archive(body, compress=True, name='temporary/mack/data/nx/output/shaders/Test.igz'):
    align = 0x800
    sectors = (len(body) + align - 1) // align
    width = 1 if sectors <= 127 else 2 if sectors <= 32767 else 4
    flag = 1 << (width * 8 - 1)
    blocks, offsets = bytearray(), []
    for j, at in enumerate(range(0, len(body), alchemy.BLOCK)):
        block = body[at:at + alchemy.BLOCK]
        use_lzma = compress if isinstance(compress, bool) else compress[j]
        offsets.append(len(blocks) // align | (flag if use_lzma else 0))
        if use_lzma:
            payload = lzma.compress(block, format=lzma.FORMAT_RAW, filters=[
                {'id': lzma.FILTER_LZMA1, 'dict_size': alchemy.BLOCK, 'lc': 3, 'lp': 0, 'pb': 2}])
            blocks += struct.pack('<IBI', len(payload), 0x5d, alchemy.BLOCK) + payload
        else:
            blocks += block
        blocks += bytes(-len(blocks) % align)
    offsets.append(len(blocks) // align)
    fmt = {1: 'B', 2: 'H', 4: 'I'}[width]
    table = struct.pack('<' + str(len(offsets)) + fmt, *offsets)
    metadata = 20 + len(table)
    data_at = (56 + metadata + align - 1) // align * align
    names_at = data_at + len(blocks)
    names = struct.pack('<I', 4) + name.encode() + b'\0'
    counts = {1: (0, 0, len(offsets)), 2: (0, len(offsets), 0), 4: (len(offsets), 0, 0)}[width]
    head = struct.pack('<14I', int.from_bytes(alchemy.MAGIC, 'little'), 12, metadata, 1, align,
                       0, 0, *counts, names_at, 0, len(names), 1)
    records = bytes(4) + struct.pack('<4I', data_at, 0, len(body), 0x20000000) + table
    return head + records + bytes(data_at - len(head) - len(records)) + blocks + names


class AlchemyArchive(unittest.TestCase):
    def decode(self, data):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'shaders.pak'
            p.write_bytes(data)
            return list(alchemy.shader_members(str(p)))

    def test_compressed_stored_and_mixed_blocks(self):
        for length, compressed in [(2000, True), (2000, False),
                                   (70000, [True, False, True]), (400000, True)]:
            with self.subTest(length=length, compressed=compressed):
                body = (b'\x01ZGIshader' * ((length + 9) // 10))[:length]
                result = self.decode(archive(body, compressed))
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0][1], body)

    def test_whole_stored_member(self):
        body = b'\x01ZGIstored shader'
        data = bytearray(archive(body, False))
        struct.pack_into('<I', data, 72, 0xff000000)
        self.assertEqual(self.decode(bytes(data))[0][1], body)

    def test_non_shader_members_are_not_decompressed(self):
        data = bytearray(archive(b'bad compressed bytes', name='textures/not_a_shader.igz'))
        struct.pack_into('<I', data, 72, 0x99000000)
        self.assertEqual(self.decode(bytes(data)), [])

    def test_malformed_layouts_are_rejected(self):
        good = archive(b'\x01ZGIshader data')
        variants = []
        for at, value, message in [(4, 13, 'version 13'), (16, 3, 'alignment'),
                                   (8, 0xffffffff, 'table sizes'), (40, len(good) + 1, 'name table'),
                                   (72, 0x200000ff, 'block indices')]:
            data = bytearray(good)
            struct.pack_into('<I', data, at, value)
            variants.append((data, message))
        data = bytearray(good)
        data[76] = 0x7f  # first sector now follows its terminal sector
        variants.append((data, 'sector range'))
        data = bytearray(good)
        data[0x800 + 4] = 0  # not supported LZMA properties
        variants.append((data, 'LZMA properties'))
        data = bytearray(good)
        struct.pack_into('<I', data, 0x800, 0x7fffffff)
        variants.append((data, 'LZMA properties or length'))
        variants.append((good[:30], 'header'))
        for data, message in variants:
            with self.subTest(message=message):
                with self.assertRaisesRegex(alchemy.Error, message):
                    self.decode(bytes(data))


if __name__ == '__main__':
    unittest.main()
