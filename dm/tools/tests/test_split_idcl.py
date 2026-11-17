"""Synthetic Switch IDCL archives: indexed references and bounded shader reads."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'dm/tools'), str(ROOT/'dm/gfx/tools')]
import idcl


def archive(packed=b'shader', size=None):
    # The first directory entry uses the second reference pair, deliberately.
    strings = [b'image', b'not_a_shader', b'renderProgResource', b'binkyuv']
    offsets, pool = [], bytearray()
    for s in strings:
        offsets.append(len(pool)); pool += s + b'\0'
    text = struct.pack('<Q4Q', 4, *offsets) + pool
    so = 120 + 144
    end = so + len(text)
    data = end + 32
    h = bytearray(120)
    h[:8] = b'IDCL\x0c\0\0\0'
    struct.pack_into('<I', h, 40, 1)
    for at, v in ((72, so), (80, end), (88, 120), (104, end), (112, data)):
        struct.pack_into('<Q', h, at, v)
    entry = bytearray(144)
    struct.pack_into('<Q', entry, 32, 2)
    struct.pack_into('<QQQ', entry, 56, data, len(packed), len(packed) if size is None else size)
    return h + entry + text + struct.pack('<4Q', 0, 1, 2, 3) + packed


class IDCLTests(unittest.TestCase):
    def read(self, blob, decode=lambda c,n: self.fail('unexpected decoder call')):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'test.resources'; p.write_bytes(blob)
            return list(idcl.shader_members(str(p), decode))

    def test_indexed_reference(self):
        self.assertEqual(self.read(archive()), [('binkyuv', b'shader')])

    def test_compressed(self):
        calls = []
        def decode(c, n):
            calls.append((c,n)); return b'decoded'
        self.assertEqual(self.read(archive(b'\x8c\x06',7),decode), [('binkyuv',b'decoded')])
        self.assertEqual(calls,[(b'\x8c\x06',7)])

    def test_truncated_payload(self):
        with self.assertRaises(ValueError): self.read(archive()[:-1])

    def test_empty_patch_alignment_past_eof(self):
        b = archive()[:120]
        struct.pack_into('<I', b, 40, 0)
        for at, v in ((72,120),(80,128),(88,120),(104,128),(112,192)):
            struct.pack_into('<Q',b,at,v)
        self.assertEqual(self.read(b + bytes(8)), [])

    def test_invalid_reference(self):
        b = archive();struct.pack_into('<Q',b,120+32,100000)
        with self.assertRaises(ValueError):self.read(b)

    def test_invalid_string(self):
        b=archive();struct.pack_into('<Q',b,120+144+8,999999)
        # Corrupt the selected kind, not an unused reference.
        struct.pack_into('<Q',b,120+144+8+2*8,999999)
        with self.assertRaises(ValueError):self.read(b)

    def test_unsupported_compression(self):
        with self.assertRaises(ValueError):self.read(archive(b'xx',7))

    def test_version(self):
        b=archive();b[4]=13
        with self.assertRaises(ValueError):self.read(b)


if __name__ == '__main__':unittest.main()
