# Wukong Black Legend

Base title ID `0100564024AEA000`, version 1.0.0, SDK 20.5.6,
Unreal Engine, NVN. Main build `c5b08250fb2273c950417d1403e961e5`.

## Status

The NSP builds on the Mac and reaches the frame loop. Its startup log shows
one vertex shader failing to load, which leaves its graphics program without
a vertex shader. The profile fix is included; gameplay and the regenerated
Metal library for that shader still need validation. iOS is untested.

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

## Validation

The existing Mac build compiled 5,275 shader libraries and completed pipeline
prebuild. The host reached `nnMain` and presented over 1,300 frames. The log
contains the missing vertex shader error above, so this does not establish
that gameplay renders correctly. The profile change requires rebuilding the
shader libraries before its effect can be confirmed.
