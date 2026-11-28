# The Witcher 3: Wild Hunt (`0100E67012924000`)

US standalone release (base game + separate Hearts of Stone `0100E67012925001` and Blood and Wine `0100E67012925002` DLCs), update 4.04b (`v262144`), SDK 15.3.0 (`d5a1029a…`, shared with [Complete Edition](../0100A0800E9C4000/README.md)), `main` `b151a224…` (different build ID from Complete Edition's `d27fd8a5…`). CD PROJEKT RED's REDengine 3 in Saber Interactive's Switch port, on NVN (18,005 shaders in the base + update RomFS). See [0100A0800E9C4000's note](../0100A0800E9C4000/README.md) for the shared rendering, shader and frame-rate background.

## What it needs

| Setting | Where | Why |
|---|---|---|
| Standard 5 GiB guest block (`mem_reserve 0x140000000`, `mem_alias 0x118000000`, `mem_stack 0x10000000`, `app_pool 0xCD500000`, `sys_resource 0x400000`) | [`game.tsv`](game.tsv) | fits an unentitled iPhone without `com.apple.developer.kernel.extended-virtual-addressing` thanks to the engine-wide allocator cut below |
| REDengine 3 virtual address reservation cut (`48 GiB → 2.75 GiB`, `alias_only=True`) | `dm/tools/engine_patches.py` | shrinks the 48 GiB VA reservation (`main+0x89e8`), 8 GiB small-block range (`main+0x4dbc`) and 32 GiB TLSF heap range (`main+0x4de0`) to 2.75 GiB / 384 MiB / 2.25 GiB for iOS; the Mac loader restores the original 48 GiB layout under its 64 GiB alias region ([REDengine 3's 48 GiB virtual address reservation](../../../docs/reference/memory.md#redengine-3s-48-gib-virtual-address-reservation)) |
| SDK 15.3.0 node-area (`1 GB → 62 MB`) and 2 MB large-region alignment cuts | `dm/tools/sdk_patches.py` | matched automatically by `MATCH_CUTS` on `sdk` `d5a1029a…` (`0x12e0f0`, `0x12e184`, `0x12e2d8`, `0x12e2e0`, `0x12e2e4`) |
| `fps_target 60`, `present_interval display`, `depth_mode zero` | [`game.tsv`](game.tsv) | 60 fps display-mode pacing and near = 0 depth mode, matching [0100A0800E9C4000](../0100A0800E9C4000/README.md#what-it-needs) |
| `shader_facts_manual.tsv` | the profile | same three shaders as Complete Edition (`11130a61f4a6f3ec`, `a52ac3530463868c`, `eacf9338c2835b9e`), all present in this release's shader map |

## Status

- **Mac (2026-11-28, Apple M6, 16 GB, macOS 27.2, `v262144` with both DLCs, partial Mac shader library of 616 shaders):**
  - **Provisional `heap_check` and `region_check`:** `heap_check` (`DM_ALIAS_SIZE=0x118000000`) passed (`heap 0.00 GB`) with no startup crash at `main+0x8924`; `region_check` (`DM_KEEP_ALIAS_CUTS=1`) measured `2.75 GB at alias +0.06 GB, returning to main+0x89f0: 2.13 GB mapped, opened up to +2.70 GB` and total reach **+3.72 GB** inside the **4.38 GB** iPhone alias region.
  - **Compact 4.375 GiB iOS layout (`DM_ALIAS_SIZE=0x118000000 DM_KEEP_ALIAS_CUTS=1`):** booted cleanly through title, initial HUD/gamma setup, main menu (both Hearts of Stone and Blood and Wine reported Installed), New Game → Fresh Start, opening movies, and into the Kaer Morhen bathtub 3D scene at **60 fps** (frame time p50 16.67 ms, p95 16.69 ms; GPU p50 5.43 ms, p95 8.21 ms; resident 2,675 MB; GPU allocated 1,363 MB). Peak alias reach under the 2.75 GiB cut was **+3.77 GiB** (`0xf189b000` inside `0x118000000`, **615 MiB** free), with TLSF mapped memory unchanged at its 1.73 GiB initial commit (`0x886b0000` mapped inside the 2.75 GiB region, `0xac9b0000` opened). The only non-partial-library `[RED]` line was `svc GetInfo: unknown info type 10 (answered 0)`.
  - **Stock 64 GiB Mac layout:** `loader.c` logged `main: 3 cuts for a small alias region undone (alias region 0x1000000000)`, restoring the original 48.00 GiB reservation (`0xa049b0000` opened) with `present cap 60 fps (game profile fps_target) applied by the present interval alone`.
- **iOS:** not yet tested on an unentitled iPhone/iPad with the 2.75 GiB cut (a reporter booted `v262144` past startup on an entitled iPhone using `DM_ALIAS_SIZE=0xE00000000` in [#3384](https://github.com/seedds/nxnative/issues/3384#issuecomment-7230126627)).

## Not checked

- Extended gameplay outside Kaer Morhen (White Orchard, Velen, Novigrad, Skellige) under the 4.375 GiB iOS alias limit, full 18,005-shader build, and on-device iOS run without `extended-virtual-addressing`.
- The open eye-adaptation histogram blow-out shared with Complete Edition ([#3048](https://github.com/seedds/nxnative/issues/3048)) was visible in bright highlights of the Kaer Morhen bathtub scene.

## Found on this game

- Resolved: static initializer crash `Result 0xe03` at `main+0x8924` and red `region_check` on iOS builds under the 4.375 GiB alias layout ([#3384](https://github.com/seedds/nxnative/issues/3384)) → [REDengine 3's 48 GiB virtual address reservation](../../../docs/reference/memory.md#redengine-3s-48-gib-virtual-address-reservation).
