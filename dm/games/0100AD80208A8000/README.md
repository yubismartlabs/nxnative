# Demon Slayer -Kimetsu no Yaiba- The Hinokami Chronicles 2 (`0100AD80208A8000`)

Switch update 2.01 (`v1114112`), Unreal Engine 5 with CRIWARE, Nintendo SDK 20.5.17, NVN 55.15. The game loads `main`, `subsdk0` (NintendoSDK_movie) and `sdk`.

## Mac validation

On Apple M6 with macOS 27.2.1 and Xcode 27.2, the game created and reloaded a save, showed the installed DLC notices and reached the first rooftop fight between Tanjiro and Daki. From launch, press A to acknowledge the autosave notice, dismiss the notices and select **Start Game**. Hold B during the opening cutscene to skip to the fight. A standing check with a shader library built for this route rendered both fighters and the arena, with the Metal HUD and audio enabled. The title ran at its stock 30 fps with a median frame time of 33.34 ms while the full shader compile ran in the background. Physical iPhone playback, online play and later chapters still need validation.

The 20.5 GB Mac app passed deep signature verification. The packaged host rendered the opening save notice using its bundled RomFS and full shader library. It built the bundled prewarm list in 2.34 seconds before its first frame. macOS performed an XProtect scan before the bundled process started on its first launch.

## Frame rate

The profile targets 60 fps through Unreal's fixed frame rate and `rhi.SyncInterval`. The shared matcher finds the engine property, its enable flag and the console variable in the base game and update 2.01. `DM_FPS_TARGET=0` restores the original limiter.

On the Apple M6 in fullscreen, update 2.01 averaged 59.9 fps over 12 seconds of the opening rooftop fight with the expanded seed. Frame time was 16.68 ms median and 17.45 ms p99, with 7.79 ms GPU time at p95. The original seed logged 8.25 seconds of pipeline compilation in long frames along the same route with the 60 fps limit. No long frame in the final run logged pipeline compilation. Prewarm took 2.59 seconds of background time against 1.44 seconds with the original seed. Later fights and iPhone frame times remain unverified.

## What it needs

- The NPDM declares 16 MiB of system resource. The shared Unreal rewriter recognizes `FMallocBinned3` and the engine's 62 GiB reservation. The Mac host kept the original reservation with its normal address space. With the 4.375 GiB alias region used by the iPhone profile, the shared gate reserved 4.06 GiB and the Mac run reached the opening fight. The SDK's existing node-area rule was selected by function match.
- The game selects near-zero NVN depth and an upper-left window origin. The profile selects the near-zero vertex entry point for offline pipeline builds.
- The `tex_dyn_slots` setting enables the existing binding for vertex programs that select buffer textures through the c2 driver tables. For example, `9e2cef6e64b83126` reads texture slots 2 and 4 at c2 + `0x170` and `0x178` and combines a texture word with sampler slot 0 at `0x568`. In the replay, all six shaders that had failed reflection conversion bound their buffer-texture arrays.
- The [prewarm seed](pso_manifest.tsv) includes 387 render and 93 compute pipelines observed on 2.01 from startup through the opening fight at 60 fps.

## Files and shaders

The merged RomFS holds 11 paks and 12 Unreal IoStore containers with version 6 tables and Oodle-compressed blocks. `pakchunk0-Switch.pak` holds `GlobalShaderCache-SP_GLSL_SWITCH.bin`. Material shaders are stored inline in the cooked packages in the export bundles. The split found 124,855 unique shaders, including 16,280 vertex, 98,061 pixel and 10,510 compute shaders and four geometry shaders. The Mac build produced a library for every key.

The opening route did not request the three aura vertex shaders (`4d968de65df61283`, `58aa1feb8d7b5c7f`, `9d68a12ad09a7160`). The fixed translator restores all nine omitted buffer-texture fetches. All three compiled for macOS and iOS with Xcode 27.2 in a targeted shader build. Their effects in gameplay remain unverified.

## Found on this game

- [Content-only Unreal paks trigger shared shader preparation](../../../docs/reference/shaders.md#content-only-unreal-paks-trigger-shared-shader-preparation). Three asset paks blocked the packer before its inline scan.
- [Unreal's fixed frame rate, found by its reflection entry](../../../docs/reference/frame-rate.md#unreals-fixed-frame-rate-found-by-its-reflection-entry) covers the packed property layout used by this game.
- [Texture slots picked at run time](../../../docs/reference/shaders.md#texture-slots-picked-at-run-time) covers the vertex shaders that select buffer textures through c2.
- [Bindless reads whose handle phi also carries other values](../../../docs/reference/shaders.md#bindless-reads-whose-handle-phi-also-carries-other-values) covers the aura shaders' resolved c1 jump-table case.
- The older 1.70 update exposed [system register accesses through x18](../../../docs/reference/rewriter.md#system-register-accesses-through-x18). The reported `mrs x18, tpidr_el0` is absent from the 2.01 `main`.
