from pkg_resources import parse_version
from pip.backwardcompat import urllib
from pip.req import InstallRequirement
from pip.index import PackageFinder
from pip.exceptions import BestVersionAlreadyInstalled, DistributionNotFound
from tests.path import Path
from tests.test_pip import here
from nose.tools import assert_raises
from mock import Mock, patch
import os

find_links = 'file://' + urllib.quote(str(Path(here).abspath/'packages').replace('\\', '/'))
find_links2 = 'file://' + urllib.quote(str(Path(here).abspath/'packages2').replace('\\', '/'))


def test_no_mpkg():
    """Finder skips zipfiles with "macosx10" in the name."""
    finder = PackageFinder([find_links], [])
    req = InstallRequirement.from_line("pkgwithmpkg")
    found = finder.find_requirement(req, False)

    assert found.url.endswith("pkgwithmpkg-1.0.tar.gz"), found


def test_no_partial_name_match():
    """Finder requires the full project name to match, not just beginning."""
    finder = PackageFinder([find_links], [])
    req = InstallRequirement.from_line("gmpy")
    found = finder.find_requirement(req, False)

    assert found.url.endswith("gmpy-1.15.tar.gz"), found

def test_duplicates_sort_ok():
    """Finder successfully finds one of a set of duplicates in different
    locations"""
    finder = PackageFinder([find_links, find_links2], [])
    req = InstallRequirement.from_line("duplicate")
    found = finder.find_requirement(req, False)

    assert found.url.endswith("duplicate-1.0.tar.gz"), found


def test_finder_detects_latest_find_links():
    """Test PackageFinder detects latest using find-links"""
    req = InstallRequirement.from_line('simple', None)
    finder = PackageFinder([find_links], [])
    link = finder.find_requirement(req, False)
    assert link.url.endswith("simple-3.0.tar.gz")


def test_finder_detects_latest_already_satisfied_find_links():
    """Test PackageFinder detects latest already satisified using find-links"""
    req = InstallRequirement.from_line('simple', None)
    #the latest simple in local pkgs is 3.0
    latest_version = "3.0"
    satisfied_by = Mock(
        location = "/path",
        parsed_version = parse_version(latest_version),
        version = latest_version
        )
    req.satisfied_by = satisfied_by
    finder = PackageFinder([find_links], [])
    assert_raises(BestVersionAlreadyInstalled, finder.find_requirement, req, True)


def test_finder_detects_latest_already_satisfied_pypi_links():
    """Test PackageFinder detects latest already satisified using pypi links"""
    req = InstallRequirement.from_line('initools', None)
    #the latest initools on pypi is 0.3.1
    latest_version = "0.3.1"
    satisfied_by = Mock(
        location = "/path",
        parsed_version = parse_version(latest_version),
        version = latest_version
        )
    req.satisfied_by = satisfied_by
    finder = PackageFinder([], ["http://pypi.python.org/simple"])
    assert_raises(BestVersionAlreadyInstalled, finder.find_requirement, req, True)

@patch('pip.pep425tags.get_supported')
def test_find_wheel(mock_get_supported):
    """
    Test finding wheels.
    """
    find_links_url = 'file://' + os.path.join(here, 'packages')
    find_links = [find_links_url]
    req = InstallRequirement.from_line("simple.dist")
    finder = PackageFinder(find_links, [], use_wheel=True)
    mock_get_supported.return_value = [('py1', 'none', 'any')]
    assert_raises(DistributionNotFound, finder.find_requirement, req, True)
    mock_get_supported.return_value = [('py2', 'none', 'any')]
    found = finder.find_requirement(req, True)
    assert found.url.endswith("simple.dist-0.1-py2.py3-none-any.whl"), found
    mock_get_supported.return_value = [('py3', 'none', 'any')]
    found = finder.find_requirement(req, True)
    assert found.url.endswith("simple.dist-0.1-py2.py3-none-any.whl"), found

