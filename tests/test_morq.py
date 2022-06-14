"""Test morq module"""
import logging
import os
import pathlib
import sys
import re
import tempfile

import pytest

from orquestra_manifest.morq import Manifest
from orquestra_manifest.utils import copy_package_file, get_package_root

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger()


class TestCommon:
    """Test the Common module"""

    @classmethod
    def setup_class(cls):
        """Setup Class properties"""
        cls.origin = os.getcwd()
        cls.manifest = Manifest()
        assert cls.manifest is not None

        package_root = get_package_root()

        cls.tmp = tempfile.TemporaryDirectory()
        cls.manifest_base = pathlib.Path(cls.tmp.name)

        test_manifest_file = package_root / "tests/data/manifest.json"
        cls.manifest_file = cls.manifest_base / "manifest.json"
        copy_package_file(test_manifest_file, cls.manifest_file)

        sys.argv = ["", "-m", cls.manifest_file.as_posix(), "init"]
        output = cls.manifest.parse_args()
        assert output is True

        cls.capsys = None
        cls.caplog = None

    @classmethod
    def teardown_class(cls):
        """Remove all test data."""
        cls.manifest.purge_repos()
        os.chdir(cls.origin)
        del cls.tmp

    @pytest.fixture(autouse=True)
    def _pass_fixtures(self, capsys):
        """Capture system messages."""
        self.capsys = capsys

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Inject caplog to capture logs.

        * https://www.py4u.net/discuss/225773
        * stackoverflow.com/questions/50373916/pytest-to-insert-caplog-fixture-in-test-method
        """
        self.caplog = caplog

    def test_morq_list(self):
        """Test the list method"""

        # Override sys.argv to simulate user inputs
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "list"]

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert outerr.out
        LOG.debug("\n%s", outerr.out)

        assert any(
            [thing for thing in str.splitlines(outerr.out) if "git@github" in thing]
        )

    def test_morq_check(self):
        """Test the check method"""

        # Override sys.argv to simulate user inputs
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "check"]

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert outerr.out
        LOG.debug("\n%s", outerr.out)

        assert any([thing for thing in str.splitlines(outerr.out) if "OK" in thing])

    def test_update_repos(self):
        """Test the check method"""
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "update"]

        output = self.manifest.parse_args()

        assert output is True

        outerr = self.capsys.readouterr()
        assert any(
            [thing for thing in str.splitlines(outerr.out) if "unchanged" in thing]
        )
        assert any(
            [thing for thing in str.splitlines(outerr.out) if "invalid" in thing]
        )

    def test_build_repos(self):
        """Test the check method"""
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "build"]

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert "nonexistant" in outerr.out

    def test_build_repos_dev(self):
        """Test the check method"""
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "dev"]

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert re.search(r'dummy.*Failed.*\n.*nonexistant', outerr.out) is not None

    def test_repos_test(self):
        """Test the check method"""
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "test"]

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        expected = ("+-------------------+--------+\n"
                    "| folder            | test   |\n"
                    "+-------------------+--------+\n"
                    "| orquestra-quantum | Failed |\n"
                    "| orquestra-opt     | Failed |\n"
                    "| orquestra-vqa     | OK     |\n"
                    "| dummy             | OK     |\n"
                    "| nonexistant       | Failed |\n"
                    "+-------------------+--------+")

        assert expected in outerr.out
