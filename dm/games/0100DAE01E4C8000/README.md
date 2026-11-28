# STORY OF SEASONS: Grand Bazaar (`0100DAE01E4C8000`)

Switch update 1.5.0 (`v655360`) over the cartridge base. Unity 6000.0.28f1 IL2CPP, Nintendo SDK 18.3.5, NVN 55.15. The game loads `main`, `subsdk0` (NintendoSDK_movie), `sdk`, and the registered `Plugins/SPFXUnityPlugin.nro`.

## What it needs

- The NPDM declares 16 MiB of system resource. Unity maps its memory in the alias region. The provisional Mac probe reached +2.85 GiB in its first 15 seconds in `nnMain`, within the profile's 4.375 GiB alias region.
- The game selects near-zero depth and an upper-left window origin. The profile prebuilds the pipelines in near-zero mode.
- The shader split found 14,249 stages in Unity data under `Data/`, the player in `main`, and the plugin. All 14,249 compiled for Mac. The 12 supplied DLC packages contain licenses for content in the game. The game displayed notifications for the add-ons at the title.

## Mac testing

On Apple M4 Pro with macOS 27.2.1 and Xcode 27.2 (27B52), the game rendered the title, DLC notices, opening sequence, and character creation. The Mac audio device opened at 48 kHz and logged no underruns during the observed opening. After the naming fix, the tester used the normal Mac keyboard dialog for the player and farm names and reported that the game looked good.

Press A at the title, dismiss each DLC notice with B, and select **New Game** and a portrait-display preference. In **Move-In Paperwork**, choose a look, fill the four fields, and press Plus to begin.

## Frame rate

The profile targets 60 fps. The shared Unity matcher finds `Application.targetFrameRate` and `QualitySettings.vSyncCount` through the internal-call table on both the cartridge base and update 1.5.0. On 1.5.0, the host changes them from 30 to 60 fps and from two vsyncs to one. `DM_FPS_TARGET=0` restores the game's original rate.

On the Apple M4 Pro, at the title with no window and the same host and shader libraries, the game sustained 30.0 fps at its original limit and 60.0 fps with the target. Median frame time went from 33.33 ms to 16.66 ms, and steady CPU power samples went from about 0.58 W to 1.16 W. With the profile default in fullscreen on the same Mac, the title presented at 60.0 fps on a 120 Hz display, with 16.67 ms frame intervals in two consecutive 300-frame samples. The base game's settings were found offline.

## Found on this game

- [The offline profanity filter's content version](../../../docs/reference/services.md#the-offline-profanity-filters-content-version) blocked both name fields. [Issue #3459](https://github.com/seedds/nxnative/issues/3459)
- [Sparse mip chains in short physical pools and repeated uploads](../../../docs/reference/nvn-objects.md#sparse-mip-chains-in-short-physical-pools) caused about 531 re-uploads per frame at the title on the M4 Pro before the texture fixes. The submission work took about 42 ms per frame there. The texture fixes were verified with synthetic NVN commands. [Issue #3459](https://github.com/seedds/nxnative/issues/3459)

## Open

- The tested scenes call two unimplemented conservative raster state setters. The log showed no enable call in the tested opening. [Conservative rasterization](../../../docs/reference/rendering.md#conservative-rasterization-remains-unimplemented)
- Base-only boot, later gameplay, and iPhone and iPad runtime remain untested. No final Mac app or IPA was built.
