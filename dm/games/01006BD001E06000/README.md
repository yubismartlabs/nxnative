# Minecraft: Nintendo Switch Edition (`01006BD001E06000`)

The 4J Studios edition for the original Switch uses NVN and Nintendo SDK 4.4.1 on update 1.0.17 (`v1114112`). The registered build combines the base NSP and that update. The standalone base version is untested.

On an M4 Pro with macOS 27.2.1, the game booted with audio, accepted a custom world name, generated an offline Survival world, saved it, and loaded it again. At the spawn point the 1920×1080 game picture ran at about 60 fps. The memory footprint settled at about 1.08 GiB during the standing-still test, which ran for over a minute.

## What it needs

- The game's NPDM declares no system resource, so the profile reports virtual address memory disabled. Its 3.14 GiB heap request fits the 3.25 GiB heap region.
- `shader_split.py` finds 12 vertex and 18 pixel shaders in `main`. The standard chain builds all 30 for Mac and iOS.
- The SDK's older VammManager functions match the existing shared SDK rewrite rules. The game has no rewriter patches of its own.
- The packaging script takes the 38 supplied add-ons. The Mac boot log confirms that the game opens their RomFS images.

## Found on this game

- Naming a world uses the SDK 4 software keyboard ABI. [The software keyboard reads the SDK's work buffer](../../../docs/reference/services.md#the-software-keyboard-reads-the-sdks-work-buffer).

## Mac playtest

Choose **Play Game**, then **Continue playing offline**. Press B to dismiss the newer-edition notice if it appears. In the **Create** tab, choose **Create New World** and select the name field to open the keyboard. For an unattended check, `DM_KBD` supplies the world name. Leave **Online Game** unchecked.

## Open

- Opening the world list logs an unbound vertex uniform slot (`cb4` in `a07ba81da2a7501a`). The captured menu and world rendered without an observed defect. [An unbound uniform slot reads the zero bank](../../../docs/reference/rendering.md#an-unbound-uniform-slot-reads-the-zero-bank).
- The unsigned iOS build needs a device playtest. Online play and local multiplayer are untested.
