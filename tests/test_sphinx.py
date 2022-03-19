"""Test common module"""
import logging
import os
import sys
import pathlib
import pytest
from orquestra_manifest.common import Manifest
from orquestra_manifest.utils import get_package_root, copy_package_file, rm_tree
from orquestra_manifest.sphinx_tools import install_sphinx, update_sphinx_conf

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger()


class TestSphinx:
    """Test the Common module"""

    @classmethod
    def setup_class(cls):
        """Setup Class properties"""
        cls.origin = os.getcwd()

        cls.manifest = Manifest()
        assert cls.manifest is not None
        package_root = get_package_root()
        cls.sphinx_base = package_root / "/tmp/sphinx/"
        cls.sphinx_base.mkdir(parents=True, exist_ok=True)

        test_manifest_file = package_root / "tests/data/manifest.json"
        cls.manifest_file = cls.sphinx_base / "manifest.json"
        copy_package_file(test_manifest_file, cls.manifest_file)

        cls.capsys = None
        cls.caplog = None

    @classmethod
    def teardown_class(cls):
        """Remove all test data."""
        # tear down self.attribute
        cls.manifest.purge_repos()
        rm_tree(cls.sphinx_base)
        os.chdir(cls.origin)

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

    def test_install_sphinx(self):
        """Test the init method"""
        # Override sys.argv to simulate user inputs
        sys.argv = ["", "-m", self.manifest_file.as_posix(), "init"]

        with self.caplog.at_level(logging.INFO):
            output = self.manifest.parse_args()
            assert output is True
            installed = install_sphinx(self.sphinx_base)
            assert installed is True
            assert "Installing a Sphinx" in self.caplog.messages[-1]

    def test_update_sphinx_conf(self):
        """Test the update_sphinx_conf() method"""
        assert update_sphinx_conf(self.manifest)
        conf_file = pathlib.Path("conf.py")
        conf_text = conf_file.read_text()
        assert "sphinx_rtd_theme" in conf_text
