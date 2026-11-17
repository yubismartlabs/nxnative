"""Read shader assets from little-endian Alchemy version 12 IGA archives.

Crash Bandicoot N. Sane Trilogy stores GLSLC outputs in IGZ members of
shaders_nx.pak. Read only shaders/*.igz; other assets need no decompression.
The archive's block tables, rather than payload heuristics, distinguish raw
blocks from LZMA blocks. No files are extracted or game-specific keys used.
"""
import lzma
import struct

from romfs import open

MAGIC = b'IGA\x1a'
BLOCK = 0x8000
MAX_SHADER_ASSET = 256 * 1024 * 1024


class Error(ValueError):
    pass


def shader_members(path):
    """Yield (archive member name, decoded bytes); reject unsupported IGA layouts.

Header: 0x38 bytes, then u32 file hashes, 16-byte file records and u32/u16/u8
block tables. A record is {offset, ordinal, decoded size, compression|index}.
The table width follows ceil(decoded size / alignment): seven, fifteen or
thirty-one bits for sector offsets; the high bit marks a compressed block.
Each member has ceil(size / 0x8000) starts and one terminal sector offset.
LZMA blocks have a u32 compressed length, five properties bytes and payload.
"""
    with open(path, 'rb') as f:
        f.seek(0, 2)
        size = f.tell()

        def read(offset, count, what):
            if offset < 0 or count < 0 or offset > size or count > size - offset:
                raise Error(f'{path}: {what} runs past the end of the IGA archive')
            f.seek(offset)
            data = f.read(count)
            if len(data) != count:
                raise Error(f'{path}: truncated {what}')
            return data

        h = read(0, 0x38, 'IGA header')
        if h[:4] != MAGIC:
            raise Error(f'{path}: not a little-endian IGA archive')
        words = struct.unpack('<14I', h)
        version, table_size, count, align = words[1:5]
        if version != 12:
            raise Error(f'{path}: unsupported Alchemy IGA version {version} (expected 12)')
        if not align or align & (align - 1) or align > BLOCK:
            raise Error(f'{path}: invalid IGA block alignment {align}')
        n32, n16, n8 = words[7:10]
        metadata = count * 20 + n32 * 4 + n16 * 2 + n8
        if metadata != table_size:
            raise Error(f'{path}: inconsistent IGA file/block table sizes')
        table = read(0x38, metadata, 'IGA file/block tables')
        names_at, names_len = words[10], words[12]
        names = read(names_at, names_len, 'IGA name table')
        if count > len(names) // 4:
            raise Error(f'{path}: IGA name-offset table is truncated')
        blocks_at = count * 20
        formats = {4: ('I', n32, blocks_at),
                   2: ('H', n16, blocks_at + n32 * 4),
                   1: ('B', n8, blocks_at + n32 * 4 + n16 * 2)}
        for i in range(count):
            no = struct.unpack_from('<I', names, i * 4)[0]
            end = names.find(b'\0', no)
            if no < count * 4 or no >= len(names) or end < 0:
                raise Error(f'{path}: invalid IGA member name offset')
            try:
                name = names[no:end].decode('utf-8')
            except UnicodeDecodeError as e:
                raise Error(f'{path}: invalid UTF-8 IGA member name') from e
            normalized = '/' + name.replace('\\', '/').lower()
            if '/shaders/' not in normalized or not normalized.endswith('.igz'):
                continue
            offset, _, length, mode = struct.unpack_from('<4I', table, count * 4 + i * 16)
            if not 0 < length <= MAX_SHADER_ASSET or offset < 0x38 + metadata or offset >= names_at:
                raise Error(f'{path}#{name}: invalid shader asset range or size')
            if mode >> 24 == 0xff:
                if length > names_at - offset:
                    raise Error(f'{path}#{name}: stored asset overlaps the IGA name table')
                yield name, read(offset, length, 'stored shader asset')
                continue
            if mode >> 24 != 0x20:
                raise Error(f'{path}#{name}: unsupported IGA compression {mode >> 24:#x}')
            sectors = (length + align - 1) // align
            width = 1 if sectors <= 0x7f else 2 if sectors <= 0x7fff else 4
            fmt, entries, at = formats[width]
            index = mode & 0xffffff
            chunks = (length + BLOCK - 1) // BLOCK
            if index > entries or chunks + 1 > entries - index:
                raise Error(f'{path}#{name}: block indices run past the IGA block table')
            values = struct.unpack_from('<' + str(chunks + 1) + fmt, table, at + index * width)
            flag = 1 << (width * 8 - 1)
            mask = flag - 1
            out = bytearray()
            for j in range(chunks):
                start = offset + (values[j] & mask) * align
                stop = offset + (values[j + 1] & mask) * align
                want = min(BLOCK, length - len(out))
                if not offset <= start < stop <= names_at:
                    raise Error(f'{path}#{name}: invalid IGA block sector range')
                if not values[j] & flag:
                    if want > stop - start:
                        raise Error(f'{path}#{name}: stored block exceeds its sector range')
                    block = read(start, want, 'stored shader block')
                else:
                    if stop - start < 9:
                        raise Error(f'{path}#{name}: LZMA block header exceeds its sector range')
                    head = read(start, 9, 'LZMA block header')
                    packed, prop, dictionary = struct.unpack('<IBI', head)
                    if prop != 0x5d or not 0 < dictionary <= BLOCK or not 0 < packed <= stop - start - 9:
                        raise Error(f'{path}#{name}: invalid IGA LZMA properties or length')
                    try:
                        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[
                            {'id': lzma.FILTER_LZMA1, 'dict_size': dictionary, 'lc': 3, 'lp': 0, 'pb': 2}])
                        # IGA LZMA is size-delimited and may omit an end marker.
                        block = decoder.decompress(read(start + 9, packed, 'LZMA payload'), max_length=want)
                    except lzma.LZMAError as e:
                        raise Error(f'{path}#{name}: invalid IGA LZMA stream') from e
                    if len(block) != want:
                        raise Error(f'{path}#{name}: LZMA block has {len(block)} bytes, expected {want}')
                out.extend(block)
            yield name, bytes(out)
