"""Test common module"""
import logging
import os
import pathlib
import pytest
import tempfile

import git
from orquestra_manifest.utils import (add_line_to_file,
                                      copy_package_file,
                                      get_package_file,
                                      get_package_root,
                                      git_pull_change,
                                      index_of_line_in_file,
                                      rm_tree,
                                      _HashCache,
                                      _print_unique,
                                      run_command
                                      )

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger()


class TestUtils:
    """Test the Common module"""
    @classmethod
    def setup_class(cls):
        """Setup Class properties"""
        cls.origin = pathlib.Path(__file__).parent.parent
        cls.tmp = tempfile.TemporaryDirectory()
        cls.tmpfile = pathlib.Path(cls.tmp.name)
        cls.syscap = None

    @classmethod
    def teardown_class(cls):
        """Remove all test data."""
        del cls.tmp

    @pytest.fixture(autouse=True)
    def _pass_fixtures(self, capsys):
        """Capture system messages."""
        self.capsys = capsys

    def test_get_package_root(self):
        """Test the get_package_root function"""
        os.chdir(self.origin)

        package_root = get_package_root()
        assert package_root.exists()

        os.chdir(self.tmpfile)
        bad_root = get_package_root()
        assert bad_root is None

        os.chdir(self.origin)

    def test_get_package_file(self):
        """Test the get_package_root function"""
        package_file = get_package_file('tests/data/manifest.json')
        assert package_file.exists()

    def test_copy_package_file(self):
        """Copy a file from this package."""
        source_file = get_package_file('tests/data/manifest.json')
        target_file = self.tmpfile / 'junk.json'
        count = copy_package_file(source_file, target_file)
        assert count == target_file.stat().st_size == source_file.stat().st_size

    def test_index_of_line_in_file(self):
        """Get line index of a line."""
        package_root = get_package_root()
        path_to_manifest = package_root / "tests/data/manifest.json"
        line = '   "version": "1.0.0",\n'
        assert index_of_line_in_file(path_to_manifest, line) >= 0

    def test_add_line_to_file(self):
        file = self.tmpfile / 'orquestra_manifest_utils.txt'
        # Create the file
        open(file, 'a', encoding='utf-8').close()

        file.write_text('checkpoint\n', encoding='utf-8')

        with open(file, encoding='utf-8') as _fd:
            assert len(list(_fd)) == 1
        add_line_to_file('added_line\n', 'checkpoint', file)
        with open(file, encoding='utf-8') as _fd:
            assert len(list(_fd)) == 2
        add_line_to_file('added_line\n', 'checkpoint', file)
        with open(file, encoding='utf-8') as _fd:
            assert len(list(_fd)) == 2

    def test_git_pull_change(self):
        path = self.tmpfile / 'junk_repo'
        repo = git.Repo.clone_from('git@github.com:heroku-python/flask-heroku.git', path)
        repo.head.reset('HEAD~8', index=True, working_tree=True)
        changed = git_pull_change(repo, 'master')
        assert changed is True
        rm_tree(path)

    def test_HashCache(self):
        H = _HashCache()
        seen = H.has_element(1)
        assert seen is False
        seen = H.has_element(1)
        assert seen is True
        # Clear and start over
        H.clear()
        seen = H.has_element(1)
        assert seen is False
        seen = H.has_element(1)
        assert seen is True

    def test_print_unique(self):
        _print_unique("hello_unique")
        out, err = self.capsys.readouterr()
        assert "hello_unique" in out
        _print_unique("hello_unique")
        out, err = self.capsys.readouterr()
        assert "hello_unique" not in out
        # New string
        _print_unique("hello_new_unique")
        out, err = self.capsys.readouterr()
        assert "hello_new_unique" in out

    def test_run_command(self):
        os.chdir(self.tmpfile)
        command = ['ls', '-l']
        run_command(command, verbose=True)
        out, err = self.capsys.readouterr()
        assert "Running:" in out

        # bad command
        command = ['cd', 'xxxyyy']
        run_command(command, verbose=False)
        out, err = self.capsys.readouterr()
        assert "No such file" in out

        run_command(command, verbose=True)
        out, err = self.capsys.readouterr()
        assert "No such file" in out

        command = ['cd', 'xxxaaa']
        run_command(command, verbose=False)
        out, err = self.capsys.readouterr()
        assert "No such file" in out
