# NARUTO SHIPPUDEN: ULTIMATE NINJA STORM 4 ROAD TO BORUTO (`01003F800CF5C000`)

Switch update 1.1.0 (v65536), SDK 8.2.1, NVN API 53.312, `main` build `d3016fc0c0402dfb70fba6b826ea772f`. CyberConnect2's engine presents through NVN and uses OpenGL ES 3.0 for the UI. The two renderers share textures and fences.

## What it needs

| Setting | Where | Why |
|---|---|---|
| 5 GiB reservation, 2.375 GiB alias region, 32 MiB system resource | [`game.tsv`](game.tsv) | The NPDM enables virtual address memory. A Mac boot measured a 2.03 GiB heap request. The configured heap region is 2.125 GiB. |
| NVN and GLSL libraries | [`gl_capture.tsv`](gl_capture.tsv) | The standard splitter finds 463 NVN stages, including 25 compute shaders. The game's OpenGL renderer compiles 387 GLSL stages at startup. |
| Modules `main`, `subsdk0`, `sdk` | [`game.tsv`](game.tsv) | `subsdk0` is NintendoSDK_movie. The host answers the GL imports. |

## Found on this game

- [An NVN sync fenced again exports a null GL fence](../../../docs/reference/rendering.md#an-nvn-sync-fenced-again-exports-a-null-gl-fence). The fix restores the title logo and button prompt.
- [A generated profile omits the OpenGL library from the app](../../../docs/reference/packing.md#a-generated-profile-omits-the-opengl-library-from-the-app). Both bundles need the OpenGL library for the game's UI.

## Frame rate

Storm 4 already asks NVN to present on every refresh. The title's display thread separately waits for two vertical blanks because the engine derives its wait from the 30 fps content rate. The same rate byte converts animation and gameplay durations authored in 30 fps units.

[`patches.py`](patches.py) selects a one-blank wait both when creating the display and when applying the rate at startup. The content rate stays at 30 so those duration conversions retain their original units. Setting the same wait before the display thread starts also avoids a 2-to-1 transition, which can strand the original counter at one.

Some Scaleform menus miss button presses and directional input with the shorter update. A movie can advance less than one timeline frame and miss the frame's input poll. On pad press, release or repeat, the patch gives the movie at least one 30 fps timeline tick. With no pad event it passes through the measured elapsed time. The rewriter applies the display and input changes together when the four functions match uniquely. The same fingerprints match base 1.0.0 and update 1.1.0.

On an Apple M4 Pro with macOS 27.2.1, update 1.1.0 averaged 59.3 fps across two 300-frame windows of a 1600 × 900 VS Battle in Hidden Leaf Village. Median frame time was 16.67–16.70 ms. A 300-frame sample from the earlier unpatched battle on that Mac averaged 30.0 fps with a 33.26 ms median. The patched match clock moved from 98 to 90 in 8.01 seconds of wall time.

The 60 fps check covered startup, the mode and team menus, stage changes and confirmation, CPU attacks, assists and pausing. The base game's functions were checked by rewriting and disassembly. Base-game gameplay, other modes, complex controls and physical iOS devices remain untested at 60 fps.

## Mac gameplay

The packaged Mac app reached active offline combat on an Apple M4 Pro with macOS 27.2.1 at 1600 × 900. The match showed both Naruto fighters, their Sasuke and Sakura support portraits, and the village arena. The app exited cleanly. From Game Mode Select, open **Free Battle**, choose an offline versus match against the CPU, then pick both teams and a stage. On the Mac keyboard, J confirms and K goes back. The game presents its license on first launch before opening the mode menu.

The 500-frame window around the battle capture had a median frame time of 41.78 ms (23.9 fps). A later 300-frame window in the same run had a median of 33.28 ms (30.0 fps). The title ran at about 24 fps before and after the fence fix.

The Mac app and unsigned IPA for 1.1.0 both contain the NVN and OpenGL libraries and the full RomFS. Other modes and physical iOS devices remain untested.

Startup logs a rejected GL sync deletion, a skipped NVN upload at mip level 6 on a texture with six levels, and a missing pipeline prewarm list. The pictured battle rendered with these warnings present.
