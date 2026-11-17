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
chain. This fork also fingerprints its imported `alchemy.py` reader. After
resolving an update that changes either file, regenerate the chain header:

```sh
python3 dm/gfx/tools/dmsh_chain.py --header
```

Include the resulting header in the reviewed merge, then rebuild affected
shader libraries and the host. A changed chain version invalidates older
compiled libraries even when the shader-map keys stay the same.
