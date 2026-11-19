# Wukong Black Legend

Base title ID `0100564024AEA000`, version 1.0.0, SDK 20.5.6,
Unreal Engine, NVN. Main build `c5b08250fb2273c950417d1403e961e5`.

## Status

The NSP builds on the Mac and reaches the frame loop. Gameplay audio runs and
the HUD appears over a black scene. The shader build reported three dropped
texture-buffer reads in vertex shader `1bcd6bca2360b49e`. The translator now
continues past unrelated loaded values to resolve the c2 table handle; rebuild
the shader library before confirming the fix. iOS is untested.

## What it needs

The game loads `main subsdk0 sdk` and uses the 20 MB system resource declared
in its NPDM. Its NVN device sets near depth to zero, so the profile selects
the matching vertex entry point for pipelines.

The provisional shader split found 5,275 programs in the Unreal shader code
archives. Shader maps and facts are included in the profile; game binaries,
extracted resources and compiled Metal libraries remain with the game files.

## Startup shader fix

The startup log reports shader `1bcd6bca2360b49e` failing reflection because
the profile had `tex_dyn_slots` disabled. Its texture handle selects an NVN
slot at run time. Enabling `tex_dyn_slots` lets reflection and replay represent
the slot-indexed texture and sampler arrays, allowing the host to load the
shader. See [Texture slots picked at run time](../../../docs/reference/shaders.md#texture-slots-picked-at-run-time).

## Gameplay scene fix

The three dropped reads came from guarded handle values in the same vertex
shader. During candidate scanning, the translator treated an unrelated loaded
value as a real buffer-texture handle and stopped before reaching the valid c2
table candidate. It now continues scanning buffer-texture phis for c2 handles.
Rebuild the shader libraries to check the scene.

## Validation

The earlier Mac build completed for 5,275 shaders and presented over 1,300
frames, but its log reports three deleted reads and does not establish that
gameplay renders correctly. The updated translator is in the chain; rebuild
the shader libraries to validate the fix.
