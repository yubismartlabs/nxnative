# Wolfenstein II: The New Colossus

Base title ID `01009040091E0000`, update v131072 (1.2), SDK 4.4.0,
id Tech 6, NVN. Main build `f2fe5ef877839f4f9334388d278366b2`, SDK build
`9de92bad67c4150268943ab4843ace65`.

## Status

Bring-up in progress on the Mac. Shader extraction is fixed; runtime and
complete Metal translation validation are pending. Published at the player's
request before completing those checks. This is not a playable-status claim.
iOS is untested.

## What it needs

The profile loads `main sdk`. The NPDM declares no system resource, so
`sys_resource 0` preserves the game's Horizon virtual-address-memory query.
The hardware application pool is `0xCD500000`, with a 4 GiB reservation,
256 MiB alias and stack regions. Startup reaches `nnMain` and opens a 48 kHz,
32-voice, six-channel audio renderer with these values.

`depth_mode zero` matches the NVN near=0 mode observed at device startup.
No game-specific rewriter patches have been added.

## Shaders

The original build stopped after finding zero programs. The three IDCL v12
resource archives hold 2,611 Oodle-compressed rendering resources; decoding them
with the game's own library exposes complete GLSLC outputs. The split yields
4,366 unique shaders: 1,663 vertex, 1,577 pixel, 543 geometry and 583 compute,
with 1,628 vertex/pixel variation pairs. All 24 IDCL archives, including
sound-only packs and empty patch packs, pass the bounded reader validation.
The shader tables contain identifiers and facts only; extracted game files and shader binaries are not committed.

## Found on this game

- [id Tech 6 IDCL rendering resources](../../../docs/reference/shaders.md#id-tech-6-idcl-rendering-resources).

## Validation

- 76 focused tests pass (IDCL, Alchemy, profile guessing and NSP chain checks).
- All 24 IDCL archives pass the final reader; the three resource archives
  contain 2,611 rendering resources. The full RomFS scan reproduces the
  shader-only scan's 4,366 programs. That earlier full scan started before
  the empty-patch correction and reported seven empty sound patches;
  the final reader validates those patches successfully.
- All 1,104 shader keys requested in the startup probe exist in the map.
  Startup reaches audio and NVN device initialization. The probe used an
  incomplete shader library, so it does not establish correct rendering,
  movie playback, audible output or gameplay.
- The full Metal compile was not validated to completion before publication.
  No iOS build or gameplay test was performed.
- The regression harness could not discover NXStudio's custom work-directory
  layout; no comparative gameplay regression result is claimed. The new
  scanner branch is limited to IDCL archives.
