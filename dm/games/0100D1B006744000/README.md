# Crash Bandicoot N. Sane Trilogy (`0100D1B006744000`)

Base game 1.0.0 (`v0`), SDK 3.5.3, Vicarious Visions' Alchemy engine with Havok,
FMOD and NVN. Modules are `main`, `subsdk0` (GLSLC) and `sdk`, in Horizon load
order. Mac gameplay and audio were tested on November 17, 2026 (macOS 27.2).
The player subsequently confirmed that the repaired game works. iOS is untested.

## What it needs

| Setting | Where | Why |
|---|---|---|
| `modules main subsdk0 sdk` | [`game.tsv`](game.tsv) | `main` imports GLSLC from `subsdk0` as well as the SDK |
| `mem_reserve 0x100000000`, `mem_alias 0x10000000`, `mem_stack 0x10000000`, `app_pool 0xCD500000`, `sys_resource 0x0` | `game.tsv` | NPDM declares no system resource; startup sets a roughly 3.14 GB heap in a 3.25 GB heap region |
| `depth_mode zero` | `game.tsv` | the game sets NVN near=0; the offline pipeline archive must select the same vertex entry point |
| Alchemy v12 IGA archive reader | `dm/gfx/tools/alchemy.py` and the accompanying `shader_split.py` patch | shader assets in `archives/shaders_nx.pak` are LZMA-compressed IGZ members |
| `shader_groups /archives/=archives` | `game.tsv` | keeps the archive shader package separate from the executable and runtime captures |

No game-specific rewriter cuts, observation gates or frame-step stubs were
needed. There is deliberately no `patches.py`. The normal shared SDK patches
and instruction rewrite remain in use. The game requests present interval 2
on a 60 Hz display, so no frame-rate override is needed.

## Shaders

The original provisional build found only 12 shaders: ten in `main` and two
runtime GLSLC captures. It continued presenting frames while reporting 109
distinct missing shader keys and an unmapped vertex shader.

The Alchemy reader decodes 84 IGZ assets from `archives/shaders_nx.pak`. It uses
the IGA file records and width-selected sector tables to distinguish stored
and LZMA blocks, validates their ranges, and passes their complete GLSLC outputs
to the existing shader reader. It has no title-ID or fixed shader-key gate.
See [Alchemy IGA shader archives](../../../docs/reference/shaders.md#alchemy-iga-shader-archives).

The complete split contains **1,635 unique shaders**: 367 vertex, 1,267 pixel and
one geometry. Source groups contain 1,623 archive shaders, ten from `main` and
two runtime captures. All 109 previously missing runtime keys are present.
The two captures are retained through the normal `DM_GLSLC_CAPTURE` mechanism;
shader binaries and capture files are not part of this profile.

The existing single-stage pixel-input-cover logic supplies 367 pairs; these
are a coverage construction, not a decoded Alchemy material pairing table.
The geometry shader has no pair observed in the tested gameplay route.

Full Mac translation on chain `d5bfb5948c60` built all 1,635 shaders, with no
undecoded bindings, no unfillable driver-bank reads and no translation losses.
All generated readable-tile, shadow-input, alpha/logic and vertex-pulling
variants compiled. A fresh split through the new scanner reproduced the exact
shader-key set of the working build; all 84 decoded assets also matched the
initial extraction byte for byte. Generated `c1_full.tsv` and `cb_extent.tsv`
are local build outputs and are not committed.

[`pso_manifest.tsv`](pso_manifest.tsv) seeds the pipeline prewarm with the local
Mac recording, including automatic shader-pair prebuild and intro/first-level
play. It contains shader and render-pipeline keys only. It is not evidence that
every shader or every level was exercised. No `validated.tsv` is supplied:
`regress.py check --record` has not validated a repository integration.

## Integration with current upstream

The YubiSmart Labs fork was integrated on top of upstream `e4b0d9b7`.
Its current chain fingerprints the shader splitter, so the Alchemy reader is
included in that inventory and the generated header is updated to
`e57be7a0d5a6`. A fresh full RomFS split produced byte-identical map, facts and
pair tables. All 1,635 shaders and their generated variants passed a full Mac
build on that chain, and the Mac host compiled successfully.

An isolated muted run of that host rendered the animated intro and title
screens for 180 seconds (over 5,100 frames), with no `[RED]` line or game crash;
the harness then ended it with SIGTERM and the host exited gracefully. The
first-level gameplay and audible-output evidence below comes from the earlier
working build, rather than a repeat full-playthrough of current upstream.
The prewarm seed omits four derived geometry-helper rows, because prewarm
resolves only base map keys and cannot load those rows directly.

## Tested on the Mac

- Game selection screen, a new Crash Bandicoot game, intro cutscene and
  N. Sanity Beach; forward movement, jumping and spinning responded correctly.
- Text, models, textures and the tested effects rendered. The roughly
  three-minute controlled test reached over 5,400 frames without a `[RED]`
  line or crash. Median frame times were about 33.3 ms (30 fps), with occasional
  loading and pipeline-compilation stalls.
- A subsequent audible run opened both DeviceOut and AudioRenderer as real
  output through MacBook Air Speakers, with stereo downmix. Callback reports
  showed zero underruns. The first automated run explicitly used `DM_AUDIO=0`;
  this was a test setting, not a missing audio implementation.
- The user's subsequent report confirms that everything appears to work.
  This does not establish complete coverage of all three games.

## Running it on the Mac

Apply the companion archive-reader patch before building from an NSP. After
installing the profile, the normal NSP script discovers the base build and
prints its launch command. Follow the repository's normal key-file setup;
this profile includes no keys or game content.

Use the printed environment, including the game's own `DM_ROMFS`, `DM_SAVE`,
`DM_MSL_DIR`, `DM_FONT_DIR` and `DM_NVN_SHMAP`, and enable `DM_WINDOW=1 DM_AUDIO=1`.
The standalone Mac host defaults to a silent audio sink when `DM_AUDIO` is
unset; `DM_AUDIO_MUTE=0` clears its diagnostic mute flag.

For `DM_CTL`: A selects a game or menu item, B jumps, Y spins, Plus skips the
opening cutscene, and `LUp` holds the forward stick direction. Screenshot
requests use `shot <absolute PNG path>`. Use separate saves for automated tests.

## Open

- Crash 2, Crash 3, later levels, bosses, completion and a long-duration run have
  not been independently exercised by the agent. Their shader assets are
  included in the census, but runtime coverage is narrower.
- Save reload and all controller mappings have not been systematically tested.
- Only base 1.0.0 is registered. Updates need a new build survey and validation;
  do not reuse fixed addresses from another version.
- iPhone/iPad memory, touch controls, iOS shaders and an unsigned IPA remain
  untested. Mac success is not an iOS validation.
- The IGA reader supports the observed little-endian version 12 layout and
  stored/LZMA shader members. Other IGA versions/compression modes are rejected.
- A broad multi-game regression run for the archive-reader integration has not
  been performed. The dispatch change is gated by the IGA magic, and its full
  real-file scan and synthetic reader tests passed.

## Found on this game

- [Alchemy IGA shader archives](../../../docs/reference/shaders.md#alchemy-iga-shader-archives).
