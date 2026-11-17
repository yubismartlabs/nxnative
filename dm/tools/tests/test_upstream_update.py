"""Fork updater: local-only Git fixtures verify preservation and review stops."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('fork_update', REPO / 'scripts/update_from_upstream.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def git(path, *args):
    return subprocess.run(['git', *args], cwd=path, capture_output=True, text=True, check=True).stdout.strip()


def commit(path, name, text):
    (path / name).write_text(text)
    git(path, 'add', name)
    git(path, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', name)


class ForkUpdate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.source = base / 'source'
        self.source.mkdir()
        git(self.source, 'init', '-b', 'main')
        commit(self.source, 'base.txt', 'base\n')
        self.fork = base / 'fork'
        subprocess.run(['git', 'clone', str(self.source), str(self.fork)], check=True, capture_output=True)
        git(self.fork, 'remote', 'add', 'upstream', str(self.source))
        self.urls = patch.object(updater, 'ALLOWED_URLS', {str(self.source)})
        self.urls.start()
        self.addCleanup(self.urls.stop)

    def update(self, merge=False):
        with contextlib.redirect_stdout(io.StringIO()):
            updater.update(self.fork, merge)

    def test_check_fetches_without_changing_head_or_working_files(self):
        before = git(self.fork, 'rev-parse', 'HEAD')
        commit(self.source, 'upstream.txt', 'incoming\n')
        self.update()
        self.assertEqual(git(self.fork, 'rev-parse', 'HEAD'), before)
        self.assertFalse((self.fork / 'upstream.txt').exists())
        self.assertNotEqual(git(self.fork, 'rev-parse', 'upstream/main'), before)

    def test_merge_keeps_local_commit_and_stops_before_commit(self):
        commit(self.fork, 'crash-profile.txt', 'local profile\n')
        before = git(self.fork, 'rev-parse', 'HEAD')
        commit(self.source, 'upstream.txt', 'incoming\n')
        # --no-commit should not need a configured identity for its prepared merge.
        git(self.fork, 'config', 'user.name', 'Fixture')
        git(self.fork, 'config', 'user.email', 'fixture@example.invalid')
        self.update(merge=True)
        self.assertEqual(git(self.fork, 'rev-parse', 'HEAD'), before)
        self.assertEqual((self.fork / 'crash-profile.txt').read_text(), 'local profile\n')
        self.assertEqual((self.fork / 'upstream.txt').read_text(), 'incoming\n')
        self.assertTrue((self.fork / '.git/MERGE_HEAD').exists())

    def test_dirty_work_is_preserved_and_merge_refused(self):
        commit(self.source, 'upstream.txt', 'incoming\n')
        before = git(self.fork, 'rev-parse', 'HEAD')
        (self.fork / 'unsaved.txt').write_text('keep this\n')
        with self.assertRaisesRegex(ValueError, 'local changes'):
            self.update(merge=True)
        self.assertEqual(git(self.fork, 'rev-parse', 'HEAD'), before)
        self.assertEqual((self.fork / 'unsaved.txt').read_text(), 'keep this\n')

    def test_unexpected_remote_is_not_replaced(self):
        git(self.fork, 'remote', 'set-url', 'upstream', '/different/source')
        with self.assertRaisesRegex(ValueError, 'somewhere other than'):
            self.update()
        self.assertEqual(git(self.fork, 'remote', 'get-url', 'upstream'), '/different/source')


if __name__ == '__main__':
    unittest.main()
