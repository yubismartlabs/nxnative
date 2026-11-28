from nso_asm import ADRP, BL, LDRX


def enable_60_fps(ctx):
    if None in ctx.others.values():
        return  # The matcher reports the missing function. Keep the original cadence.

    display_init = ctx.others['display initialization'] + 0x118
    rate_setter = ctx.others['rate setter'] + 0x28
    movie_advance = ctx.base + 0x20c
    pad_slot = ctx.address(ctx.others['pad state'])

    ctx.site(display_init, '2809c81a')    # udiv w8, w9, w8
    ctx.site(rate_setter, '2409c81a')     # udiv w4, w9, w8
    ctx.site(movie_advance, '000140f9')   # ldr x0, [x8]

    # At 60 fps a 30 fps Scaleform timeline can skip the poll for a one-tick
    # pad event. Give it one full timeline tick on input; idle updates use
    # the elapsed time supplied by the game.
    advance = ctx.here()
    ctx.emit(ADRP(10, ctx.here(), pad_slot))
    ctx.emit(LDRX(10, 10, (pad_slot & 0xfff) // 8))
    ctx.emit(LDRX(10, 10))
    ctx.emit(0xb400022a)  # cbz x10, load_movie
    ctx.emit(LDRX(9, 10, 0x60 // 8))  # player 1 press and release
    ctx.emit(0xb940714b)  # ldr w11, [x10, #0x70] (repeat)
    ctx.emit(0xaa0b0129)  # orr x9, x9, x11
    for pad in (0xb0, 0x160):
        ctx.emit(LDRX(11, 10, (pad + 0x60) // 8))
        ctx.emit(0xaa0b0129)  # orr x9, x9, x11
        ctx.emit(0xb940014b | ((pad + 0x70) // 4) << 10)  # ldr w11, [x10, #repeat]
        ctx.emit(0xaa0b0129)  # orr x9, x9, x11
    ctx.emit(0xb40000a9)  # cbz x9, load_movie
    ctx.emit(0x52911129)  # mov w9, #0x8889
    ctx.emit(0x72a7a109)  # movk w9, #0x3d08, lsl #16 (1/30 s as a float)
    ctx.emit(0x1e270121)  # fmov s1, w9
    ctx.emit(0x1e216800)  # fmaxnm s0, s0, s1
    ctx.emit(LDRX(0, 8))  # load_movie: original ldr x0, [x8]
    ctx.emit(0xd65f03c0)  # ret

    # Keep the content rate in the game object. Only the wait for two
    # vertical blanks becomes one, including before the wait thread starts.
    ctx.put(display_init, [0x52800028], 'Initialize the display wait to one vertical blank')
    ctx.put(rate_setter, [0x52800024], 'Keep a one-blank wait when applying the content rate')
    ctx.put(movie_advance, [BL(movie_advance, advance)], 'Advance Scaleform a full tick on a pad event')


rate = 'Storm 4 60 fps display cadence and Scaleform input'

# One set of functions matches the base game and update. Apply all three
# changes together, using the game's own pad snapshot code to find its data.
MATCH_STUBS = {'main': [
    {'name': rate, 'size': 0x2ac,
     'fingerprints': ['118922bab9296660dbed513211950f91f1b828b42701360e924b9470b527e49e'],
     'stub': enable_60_fps,
     'others': {
         'display initialization': {
             'size': 0x2b4,
             'fingerprints': ['fdc9e28f7c7ab2f6e5ebc14db0a429e98b20ec08d629f0dea9b8bb16698dd5a6'],
         },
         'rate setter': {
             'size': 0x48,
             'fingerprints': ['2fef4323f1759fba58c8e9e0711f7cb0e296d460758eed8bd04768ee4eaa3e54'],
         },
         'pad state': {
             'size': 0x178,
             'fingerprints': ['8c4d3a5c2ad8227a2c9b789c63eb83c5cd7079180d1181f8c80beb7edc1ad30b'],
         },
     }},
]}

BINDING = [
    {'what': rate, 'now': 'game', 'goal': 'game', 'purpose': 'frame rate',
     'checked': 'Display setup, rate setter, Scaleform advance and pad snapshot share fingerprints in 1.0.0 and 1.1.0',
     'why': 'Storm 4 uses the native rate to convert game content durations and its 30 fps movies poll the game pad state. The host already honors a one-refresh present interval.'},
]
