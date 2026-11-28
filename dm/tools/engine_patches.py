# The rewriter's engine-wide function patches: fixes of middleware code (Unity, Unreal, ...) that hold for every game shipping that engine code, matched by function
# (dm/tools/nso_match.py) in every game's module of the named kind, whatever the profile and with no build ID. dm/tools/patch_nso.py applies them as it does
# sdk_patches.py's MATCH_CUTS: to a module whose build has no CUTS, with a plain line (no red) where nothing matches, as most games ship other engines. A game's own
# patches.py holds what only that game needs; sdk_patches.py holds Nintendo's SDK. Profiles can also import a shared rule to opt in.

import struct

from loader_census import adrp, got_values, ldr64
from nso_match import MatchError


def check_redengine_va_reserve(module, start):
    # Verify the bl at +0x14 targets the PLT stub for nn::os::AllocateAddressRegion(uintptr_t*, size_t).
    call_pc = start + 0x14
    w = struct.unpack_from('<I', module.image, call_pc)[0]
    if (w & 0xfc000000) != 0x94000000:
        raise MatchError('virtual-address initializer does not call at +0x14')
    imm26 = w & 0x3ffffff
    if imm26 & (1 << 25): imm26 -= 1 << 26
    plt = call_pc + imm26 * 4
    if not 0 <= plt <= module.text_end - 16:
        raise MatchError('virtual-address initializer call target is outside text')
    w0, w1, _, w3 = struct.unpack_from('<IIII', module.image, plt)
    page = adrp(w0, plt)
    load = ldr64(w1)
    if page is None or load is None or page[0] != 16 or load[:2] != (17, 16) or w3 != 0xd61f0220:
        raise MatchError('virtual-address initializer does not target a standard PLT stub')
    got = page[1] + load[2]
    img = module.image
    mod0 = struct.unpack_from('<I', img, 4)[0]
    if img[mod0:mod0 + 4] != b'MOD0':
        raise MatchError('missing MOD0 header')
    dyn = mod0 + struct.unpack_from('<i', img, mod0 + 4)[0]
    tags = {}
    for k in range(4096):
        t, v = struct.unpack_from('<qQ', img, dyn + k * 16)
        if t == 0: break
        tags.setdefault(t, v)
    if not {2, 5, 6, 23} <= tags.keys():
        raise MatchError('missing dynamic relocation tables')
    symtab, strtab, jmprel, pltrelsz = tags[6], tags[5], tags[23], tags[2]
    for off in range(jmprel, jmprel + pltrelsz, 24):
        r_off, r_info, _ = struct.unpack_from('<QQq', img, off)
        if r_off == got:
            name_off = struct.unpack_from('<I', img, symtab + (r_info >> 32) * 24)[0]
            end = img.index(b'\0', strtab + name_off)
            sym = bytes(img[strtab + name_off:end]).decode('latin1')
            if sym != '_ZN2nn2os21AllocateAddressRegionEPmm':
                raise MatchError(f'virtual-address initializer calls {sym}, not nn::os::AllocateAddressRegion')
            return
    raise MatchError('virtual-address initializer PLT slot has no JMPREL entry')


def check_lets_go_period_table(module, start):
    # Match the relocated table behind the constructor's ADRP/LDR, whose
    # address the fingerprint normalizes across builds.
    page_word, load_word = struct.unpack_from('<II', module.image, start + 0xc0)
    page = adrp(page_word, start + 0xc0)
    load = ldr64(load_word)
    if page is None or load is None or page[0] != load[1]:
        raise MatchError('the frame-period table load does not match')
    table = got_values(module.image).get(page[1] + load[2])
    periods = struct.pack('<QQ', 16_666_667, 33_333_334)
    if table is None or table < module.text_end or module.image[table:table + len(periods)] != periods:
        raise MatchError('the first two frame periods are not 16,666,667 and 33,333,334 ns')


# Both Let's Go profiles import this rule through their MATCH_CUTS. The framework constructor initializes the
# periods that drive presentation and simulation. Their application override
# resets the simulation period every update, so the two cuts apply together.
lets_go_frame_periods = {
    'name': 'one-tick render and simulation periods',
    'functions': [
        {'size': 0x224,
         'fingerprints': ['2ceb7798508227178c3b40a4a1cab7d56793ccedf9727f84185b533edc596b94'],
         'check': check_lets_go_period_table,
         'cuts': [(0xc8, '080540f9', '080140f9', 'initialize both frame periods from the one-tick entry')]},
        {'size': 0x18,
         'fingerprints': ['81673279c08d7094e975f22e4d974b45e6b994714cb3257a3ff11ccb06bba883'],
         'cuts': [(0x10, 'e2030032', '02008052', 'select the one-tick simulation period on every update')]},
    ],
}

lets_go_frame_period_binding = [{
    'what': 'one-tick render and simulation periods',
    'now': 'game', 'goal': 'game', 'purpose': 'frame rate',
    'why': "the profiles choose a faster default and the game's application override sets the simulation period. Both functions and the relocated period table must match",
    'checked': 'Pikachu and Eevee 1.0.0 and 1.0.2 match both functions and the period table offline',
}]


MATCH_CUTS = {'main': [
    # Unity 2018's ThreadedStreamBuffer, the ring buffer every Unity worker thread is fed through (UnityGfxDeviceWorker, BatchDeleteObjects, ...), wakes a sleeping side with a Dekker
    # handshake on two words. The reader that finds nothing to read sets its "reader sleeping" flag (+0x118) with a store-release and loads the write position (+0x80) again before
    # sleeping on its semaphore; a writer stores the write position with a store-release and then checks that flag. The mirror pair: a writer short of space sets "writer sleeping"
    # (+0xd8) and loads the read position (+0x40) again, and the reader stores the read position and checks that flag. The second access of each side is a plain ldr, and AArch64
    # lets a plain load complete before an earlier store-release is visible (store → load order needs a load-acquire or a barrier), so both sides can read the old value and neither
    # wakes the other. The Switch's Cortex-A57 did not show it; on Apple cores it happened within seconds in 3 of 5 Mac runs of FINAL FANTASY CRYSTAL CHRONICLES Remastered Edition:
    # the main thread posts a command to UnityGfxDeviceWorker and waits on that command's semaphore while the worker sleeps on its own with the command in the buffer, every other
    # thread then waits on the main thread and the game never presents a frame. Each of those plain loads becomes a load-acquire (ldar), which a store-release before it orders after
    # the store: 14 of 14 runs booted and kept presenting (the game's note). The cause is in the engine's code, which the rewriter changes deliberately.
    # Checked 2026-11-09: FINAL FANTASY CRYSTAL CHRONICLES Remastered Edition 1.0.3 (Unity 2018.4.2f1, the registered cuts until then; rewritten byte-identical) and 1.0.0 (the
    # same eight sites 0x25380 earlier, which no cut covered), and Raging Loop 1.0.0 (Unity 2018.3.10f1): the same four functions, instruction for instruction; the fourth calls a log
    # helper of another body in the other two builds, hence its three fingerprints.
    # Checked 2026-11-20: Untitled Goose Game 1.1.2 (Unity 2018.4.1f1): the first three functions match at main+0x182ed20, +0x182f310 and +0x182f650. The fourth
    # (main+0x182fa50) calls a different log helper and keeps the stlr w25 to +0xd8 and the ldr of +0x40 at +0x168. Unity 2017.4 (Cuphead, AI: THE SOMNIUM FILES) has other code there, not reviewed.
    # Thronebreaker 1.0.2 (Unity 2018.4.2f1) keeps the same writer-sleep handshake and the plain load at +0x168. Its game note records the ordering test.
    {'name': 'Unity 2018 ThreadedStreamBuffer: load-acquires after its store-releases', 'functions': [
        # the reader going to sleep (FINAL FANTASY CRYSTAL CHRONICLES 1.0.3 main+0x1e67930)
        {'size': 528, 'fingerprints': ['6b48e9a19281a61d041d534127efd9514bcfd37c971463d342ed1ffe3bde0630'], 'cuts': [
            (0x120, '080140b9', '08fddf88', 'stream reader going to sleep: ldr w8,[x8] → ldar (write position after the store-release of "reader sleeping")')]},
        # the reader (main+0x1e67f20)
        {'size': 824, 'fingerprints': ['ee4b0475ad2c62eb78283eaac6b27c094b08fe8542f906fe02ad25c68944204b'], 'cuts': [
            (0x13c, '080140b9', '08fddf88', 'stream reader: ldr w8,[x8] → ldar ("writer sleeping" after the store-release of the read position)'),
            (0x234, '080140b9', '08fddf88', 'stream reader: ldr w8,[x8] → ldar ("writer sleeping" after the store-release of the read position)'),
            (0x2b8, '080140b9', '08fddf88', 'stream reader: ldr w8,[x8] → ldar ("writer sleeping" after the store-release of the read position)')]},
        # the writer (main+0x1e68260)
        {'size': 828, 'fingerprints': ['e2c1c6cb95191a9a2a7694e03f0f6304a9b54058d92795c5a25b3e56d7da0a2e'], 'cuts': [
            (0x148, '080140b9', '08fddf88', 'stream writer: ldr w8,[x8] → ldar ("reader sleeping" after the store-release of the write position)'),
            (0x238, '080140b9', '08fddf88', 'stream writer: ldr w8,[x8] → ldar ("reader sleeping" after the store-release of the write position)'),
            (0x2bc, '080140b9', '08fddf88', 'stream writer: ldr w8,[x8] → ldar ("reader sleeping" after the store-release of the write position)')]},
        # the writer going to sleep (main+0x1e68660; Raging Loop's and FINAL FANTASY CRYSTAL CHRONICLES 1.0.0's call a log helper of another body)
        {'size': 576, 'fingerprints': ['aa8a3dc16b30ea6c510161b632162019a41a95b81a71ccf909d439a08691b1b6', '57a283d159be07dc3178d4158ddecd7c4ebb34e6631a7965111c38c02724b2f2',
                                     'eb41f41ceeffc7e1428740e81625bc7b8aa12aa6823cf1fd4152e50e752e2d4f', '1ef244e58a3747e8662a00de83267f6eb3add6bdc8bb0f93639f08eada3e74bb',
                                     'e1bff2e6d23005e70825edfaa2b79abb67f475c3615a6d364cebc76befd49815'], 'cuts': [
            (0x168, '290140b9', '29fddf88', 'stream writer going to sleep: ldr w9,[x9] → ldar (read position after the store-release of "writer sleeping")')]},
    ]},

    # REDengine 3 (The Witcher 3: Wild Hunt) reserves a 48 GiB address region in DT_INIT_ARRAY[0] without checking the result, then bumps four sub-ranges sequentially out of it:
    # 8 GiB for the small-block slab allocator (which pre-commits exactly 340 x 1 MiB slabs = 340 MiB once and recycles them), 32 GiB for the main TLSF heap (initial commit
    # 0x6e900000 = 1.7275 GiB, growing in 4 MiB steps, TLSF table sized dynamically from end - start), 33.7 MiB (0x21b0000) for a fixed TLSF pool, and 40 MiB for a 2 x 20 MiB pool.
    # Nothing places fixed offsets inside the 48 GiB region. On iOS without the extended-virtual-addressing entitlement, the 48 GiB reservation fails and the first 1 MiB commit
    # traps with 0xe03. Shrinking the reservation to 2.75 GiB (384 MiB small-block + 2.25 GiB TLSF + 73.7 MiB fixed pools = 2.697 GiB) leaves >530 MiB of TLSF growth headroom
    # (more than the Switch's 3.21 GiB app pool can physically commit beside the fixed and GPU pools) and ~615 MiB of room for separate regions inside the standard 4.375 GiB iPhone
    # alias region. Marked alias_only so the Mac loader restores the original 48 / 8 / 32 GiB instructions under its 64 GiB alias region (GitHub issue #3384).
    {'name': 'REDengine 3 virtual address reservation: 48 GiB → 2.75 GiB for iOS alias region', 'alias_only': True, 'functions': [
        # 4.04b (0100E67012924000 v262144: main+0x89d8, main+0x4db0)
        {'size': 40, 'fingerprints': ['cf21ec09194b61c5ab5089baa0e6828d81e59b53fc934b7ae717abf9e0e8c05a'],
         'check': check_redengine_va_reserve, 'cuts': [
            (0x10, '8101c0d2', '0100b6d2', 'REDengine 3 VA reservation: mov x1,#0xc00000000 (48 GiB) → #0xb0000000 (2.75 GiB)')]},
        {'size': 104, 'fingerprints': ['7234b1b192c7cd2c2e41d3de09ed19705e1e99c341cbc0b4dc9e0918ffb9cf35'], 'cuts': [
            (0x0c, '4900c0d2', '0900a3d2', 'REDengine 3 small-block VA range: mov x9,#0x200000000 (8 GiB) → #0x18000000 (384 MiB)'),
            (0x30, '0901c0d2', '0900b2d2', 'REDengine 3 TLSF heap VA range: mov x9,#0x800000000 (32 GiB) → #0x90000000 (2.25 GiB)')]},
    ]},
    {'name': 'REDengine 3 virtual address reservation: 48 GiB → 2.75 GiB for iOS alias region', 'alias_only': True, 'functions': [
        # 3.7 (0100E67012924000 v0: main+0x350f80, main+0x34dff0)
        {'size': 40, 'fingerprints': ['43e8e08ff50941a5a62ab644eb293732d0b1bc859d50efabef60dd7e1fd50342'],
         'check': check_redengine_va_reserve, 'cuts': [
            (0x10, 'e1075eb2', '0100b6d2', 'REDengine 3 VA reservation: mov x1,#0xc00000000 (48 GiB) → #0xb0000000 (2.75 GiB)')]},
        {'size': 124, 'fingerprints': ['22b574f20fe0a891908c0e2659d6cc43232ee8d851e5d9afe01995480e2b2170'], 'cuts': [
            (0x14, 'e9035fb2', '0900a3d2', 'REDengine 3 small-block VA range: mov x9,#0x200000000 (8 GiB) → #0x18000000 (384 MiB)'),
            (0x40, 'e8035db2', '0800b2d2', 'REDengine 3 TLSF heap VA range: mov x8,#0x800000000 (32 GiB) → #0x90000000 (2.25 GiB)')]},
    ]},
]}
