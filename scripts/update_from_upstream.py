#!/usr/bin/env python3
"""Fetch official NXNative updates; optionally prepare an uncommitted merge."""
import argparse
from pathlib import Path
import subprocess
import sys

UPSTREAM = 'https://github.com/seedds/nxnative.git'
ALLOWED_URLS = {UPSTREAM, UPSTREAM.removesuffix('.git'),
                'git@github.com:seedds/nxnative.git',
                'ssh://git@github.com/seedds/nxnative.git'}


def git(repo, *args, capture=True):
    return subprocess.run(['git', *args], cwd=repo, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None, check=True)


def update(repo, merge=False):
    repo = Path(repo).resolve()
    git(repo, 'rev-parse', '--show-toplevel')
    if merge:
        git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
        for state in ['MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD']:
            path = Path(git(repo, 'rev-parse', '--git-path', state).stdout.strip())
            if not path.is_absolute():
                path = repo / path
            if path.exists():
                raise ValueError('Finish the existing Git operation before merging upstream.')
        if git(repo, 'status', '--porcelain').stdout.strip():
            raise ValueError('The working tree has local changes. Commit or preserve them before merging upstream.')
    remote = subprocess.run(['git', 'remote', 'get-url', 'upstream'], cwd=repo,
                            text=True, capture_output=True)
    if remote.returncode:
        git(repo, 'remote', 'add', 'upstream', UPSTREAM)
    elif remote.stdout.strip() not in ALLOWED_URLS:
        raise ValueError('The upstream remote points somewhere other than seedds/nxnative. Check it before updating.')
    git(repo, 'fetch', '--prune', 'upstream', 'main', capture=False)
    local, incoming = map(int, git(repo, 'rev-list', '--left-right', '--count',
                                   'HEAD...upstream/main').stdout.split())
    print(f'Current branch: {local} local commits; upstream: {incoming} incoming commits.', flush=True)
    if not incoming:
        print('This branch already contains the fetched upstream main.')
        return
    if not merge:
        print('Review with: git log --oneline HEAD..upstream/main')
        print('Prepare a merge with: python3 scripts/update_from_upstream.py --merge')
        return
    # --no-ff makes even a fast-forward stop for review; --no-commit prevents an
    # automatic merge commit. Never reset, rebase, stash or push the user's work.
    result = subprocess.run(['git', 'merge', '--no-commit', '--no-ff', 'upstream/main'], cwd=repo)
    if result.returncode:
        print('The merge needs attention. Inspect git status and resolve conflicts, or use git merge --abort.', file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)
    print('Merge prepared. Review the diff, run the required checks, then commit and push when ready.')
    print('Rebuild game shaders and the host when upstream changes their inputs or translation chain.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--merge', action='store_true', help='prepare an upstream merge without committing or pushing it')
    args = parser.parse_args()
    try:
        update(Path(__file__).resolve().parents[1], args.merge)
    except (ValueError, subprocess.CalledProcessError) as e:
        detail = e.stderr.strip() if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        print(f'Update stopped: {detail}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
