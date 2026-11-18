# Updating the YubiSmart Labs fork

The official source is [seedds/nxnative](https://github.com/seedds/nxnative).
This fork also carries the [Crash Bandicoot N. Sane Trilogy profile](../dm/games/0100D1B006744000/README.md)
and the Alchemy archive reader needed to reproduce its shaders.

## Check for updates

Run this from your checkout:

```sh
python3 scripts/update_from_upstream.py
```

The script configures the `upstream` remote if it is missing, fetches official
`main`, and reports the current branch's local and incoming commit counts.
It leaves your branch and files as they are. Your GitHub fork does not update
on a schedule, and this command does not push anything.

Review incoming commits with `git log --oneline HEAD..upstream/main`.
To prepare their merge into your current branch:

```sh
python3 scripts/update_from_upstream.py --merge
```

Commit or otherwise preserve local file changes first. The script refuses an
uncommitted working tree, a detached HEAD, an existing merge/rebase/cherry-pick,
or an `upstream` remote pointing elsewhere. It never resets, rebases, stashes
or pushes your work. A merge stops before creating a commit, including when a
fast-forward would otherwise be possible.

Review `git status` and `git diff --cached`, resolve any conflicts and run the
required checks before committing and pushing to your fork. If you decide not
to continue the prepared merge, `git merge --abort` cancels it.

Changes to the shader translation chain or a game's shader inputs require a
full shader rebuild and a host rebuild as described in [development](development.md).
Keep each game's extracted assets and caches outside this repository. Updates
may require merging changes to the Alchemy reader or shader splitter.

The script and merge workflow are manual. Merging an upstream update does not
establish that every local game still works: use the regression workflow and
play the affected games before treating the update as validated.

## Shader-chain metadata in this fork

Current upstream fingerprints `shader_split.py` as part of the translation
chain. This fork also fingerprints its imported `alchemy.py` and `idcl.py` readers. After
resolving an update that changes either file, regenerate the chain header:

```sh
python3 dm/gfx/tools/dmsh_chain.py --header
```

Include the resulting header in the reviewed merge, then rebuild affected
shader libraries and the host. A changed chain version invalidates older
compiled libraries even when the shader-map keys stay the same.

## Reviewed upstream merge: 2026-11-18

- Official main incorporated through `0b5fd602` (50 incoming commits).
- Fork main before the merge: `b59ac4d5`, preserved on
  `backup/before-upstream-2026-11-18` on origin.
- All six fork-only commits are retained in the merge history. The Crash,
  Burnout and Wolfenstein profiles, Alchemy and IDCL readers, AVC picture-order
  fix, and manual update script remain present.
- Unfinished Wolfenstein depth-prepass work is separately preserved at
  `4fd7b8ad` on `wip/wolfenstein-depth-prepass-2026-11-18`; it is not included
  in this main-branch update. Purple rendering remains under investigation.
- The only conflict was the generated `dmsh_chain.h`; it was regenerated from
  the combined source tree. The resulting chain is `a83fdd39d6b1`.
- Validation: 92 focused Python tests pass, shader-tool integrity passes,
  and the native AVC suite passes, including adaptive picture order and
  upstream's NV12 color-key cases. No gameplay or full shader rebuild was
  performed for this merge.

Rebuild each game's shader libraries and host before using this updated source
with that game. Existing binaries and libraries belong to the older chain.
