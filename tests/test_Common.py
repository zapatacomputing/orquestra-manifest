"""Test common module"""
import logging
import sys
import pytest
from orquestra_manifest.common import Manifest
from orquestra_manifest.utils import get_package_root


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger()


class TestCommon:
    """Test the Common module"""
    @classmethod
    def setup_class(cls):
        """Setup Class properties"""
        # configure self.attribute
        cls.manifest = Manifest()
        assert cls.manifest is not None
        package_root = get_package_root()

        cls.manifest_file = package_root / 'tests/data/manifest.json'
        sys.argv = ['', '-m', cls.manifest_file.as_posix(), 'init']
        output = cls.manifest.parse_args()
        assert output is True

        cls.capsys = None
        cls.caplog = None

    @classmethod
    def teardown_class(cls):
        """Remove all test data."""
        cls.manifest.purge_repos()

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

    def test_common_list(self):
        """Test the list method"""

        # Override sys.argv to simulate user inputs
        sys.argv = ['', '-m', self.manifest_file.as_posix(), 'list']

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert outerr.out
        LOG.debug('\n%s', outerr.out)

        assert any([thing for thing in str.splitlines(outerr.out) if 'git@github' in thing])

    def test_common_check(self):
        """Test the check method"""

        # Override sys.argv to simulate user inputs
        sys.argv = ['', '-m', self.manifest_file.as_posix(), 'check']

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert outerr.out
        LOG.debug('\n%s', outerr.out)

        assert any([thing for thing in str.splitlines(outerr.out) if 'OK' in thing])

    def test_update_repos(self):
        """Test the check method"""
        sys.argv = ['', '-m', self.manifest_file.as_posix(), 'update']

        output = self.manifest.parse_args()
        assert output is True

        outerr = self.capsys.readouterr()
        assert any([thing for thing in str.splitlines(outerr.out) if 'Unchanged' in thing])
