"""Test common module"""
import logging
import os
import pathlib

import git
from orquestra_manifest.utils import (add_line_to_file,
                                      copy_package_file,
                                      get_package_file,
                                      get_package_root,
                                      git_pull_change,
                                      index_of_line_in_file,
                                      rm_tree
                                      )

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger()


class TestUtils:
    """Test the Common module"""
    @classmethod
    def setup_class(cls):
        """Setup Class properties"""
        cls.origin = str(pathlib.Path().resolve())

    @classmethod
    def teardown_class(cls):
        """Remove all test data."""

    def test_get_package_root(self):
        """Test the get_package_root function"""
        os.chdir(self.origin)

        package_root = get_package_root()
        assert package_root.exists()

        badpath = pathlib.Path('/tmp/')
        os.chdir(badpath)
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
        target_file = pathlib.Path('/tmp/junk.json')
        count = copy_package_file(source_file, target_file)
        assert count == target_file.stat().st_size == source_file.stat().st_size

    def test_index_of_line_in_file(self):
        """Get line index of a line."""
        package_root = get_package_root()
        path_to_manifest = package_root / "tests/data/manifest.json"
        line = '   "version": "1.1.0",\n'
        assert index_of_line_in_file(path_to_manifest, line) >= 0

    def test_add_line_to_file(self):
        file = pathlib.Path('/tmp/orquestra_manifest_utils.txt')
        with open(file, 'a', encoding='utf-8'):
            pass
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
        path = pathlib.Path('/tmp/junk_repo')
        rm_tree(path)
        repo = git.Repo.clone_from('git@github.com:heroku-python/flask-heroku.git', path)
        repo.head.reset('HEAD~8', index=True, working_tree=True)
        changed = git_pull_change(repo, 'master')
        assert changed is True
        rm_tree(path)
