"""Utils for this package"""
import logging
import os
import pathlib
import subprocess
from enum import Enum, unique

import git
from git.exc import BadName, GitCommandError, InvalidGitRepositoryError

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("orquestra_manifest.utils")


@unique
class RefType(Enum):
    """Formalize the reference type for Git reference"""

    BRANCH = 1
    TAG = 2
    COMMIT = 3
    UNKNOWN = 4


class _HashCache:
    """Keep track of what was hashed"""

    cache: set([int]) = set()

    def has_element(self, hashed):
        """Test if element is present, add it if not"""
        if hashed in self.cache:
            return True
        self.cache.add(hashed)
        return False

    def clear(self):
        """Clear the cache"""
        self.cache = set()


def _print_unique(message):
    """Print all unique messages not in _HashCache"""
    hashcache = _HashCache()
    hashed = hash(message)
    if not hashcache.has_element(hashed):
        print(message)


def run_command(command, stdout=False, verbose=False):
    """Run a command, handle output.

    * Command : list of system strings.
    * Return : (int) the return code of the process, per Posix conventions.
    """

    if verbose:
        print(f"Running: {command}")

    try:
        proc = subprocess.run(command, shell=False, capture_output=True)
    except Exception as ex:
        print(f"Exception running command {command}: {ex}")
        return ex.errno

    if stdout:
        print(proc.stdout.decode())

    if verbose:
        print(proc.stderr.decode())
    else:
        _print_unique(proc.stderr.decode())

    return proc.returncode


def folder_cmd(folder, cmd, verbose=False, stdout=False):
    """Execute cmd on pathlib.Path folder"""
    error = 0
    folder_name = folder.resolve().name
    cmd_string = " ".join(cmd)
    LOG.info("Executing '%s' on %s", cmd_string, folder_name)
    LOG.info("-" * 60)
    try:
        os.chdir(folder)
        error = run_command(cmd, verbose=verbose, stdout=stdout)
    except Exception as ex:
        LOG.warning("Failed to '%s' on %s: %s", cmd_string, folder_name, ex)
        error = 100
    return error


def get_package_root():
    """Get the root path of the current package, using Git.

    Returns: pathlib.Path() if exists, or None
    """
    path = pathlib.Path()
    try:
        git_repo = git.Repo(path, search_parent_directories=True)

    except InvalidGitRepositoryError:
        LOG.warning("Invalid Git path: %s", path.resolve())
        return None

    except Exception as ex:
        LOG.warning("Problem with path: %s:: %s", path.resolve(), ex)
        return None

    root = pathlib.Path(git_repo.working_tree_dir)
    if not root.exists():
        LOG.warning("No package root exists: %s", root)
        return None
    return root


def get_package_file(file_name):
    """Get the file path of the current package, using Git.
    Why: So we can retreive configuration files based in the package.

    Returns: pathlib.Path() if exists, or None.
    """
    root_path = get_package_root()
    if not root_path:
        return None

    file = root_path / file_name
    if not file.exists():
        LOG.warning("No such file exists: %s", file)
        return None

    return file


def copy_package_file(from_file, to_file):
    """Copy from_file to to_file.
    Inputs:
       * from_file: pathlib.Path()
       * to_file:   pathlib.Path()

    Returns: count of chars copied
    """
    count = 0
    root_path = get_package_root()
    if not root_path:
        return count

    try:
        count = to_file.write_text(from_file.read_text())
    except FileNotFoundError as ex:
        LOG.critical("No such file exists: %s", ex)
    except PermissionError as ex:
        LOG.critical("Permission Error: %s", ex)

    return count


def index_of_line_in_file(file, match_line):
    """Get index of line match_line"""
    with open(file, "r", encoding="utf-8") as _fd:
        for (i, line) in enumerate(_fd):
            if match_line in line:
                return i
    return -1


def add_line_to_file(add_line, match_line, file):
    """Add a line to file at match_line.

    It may not be efficient, but its readable.
    """
    index = index_of_line_in_file(file, match_line)

    with open(file, "r+", encoding="utf-8") as _fd:
        contents = _fd.readlines()

        if index == len(contents) - 1:
            contents.append(add_line)
        elif contents[index + 1] != add_line:
            contents.insert(index + 1, add_line)

        _fd.seek(0)
        _fd.writelines(contents)


def append_string_to_file(string, path):
    """Append to a pathlib file: path"""
    with path.open("a") as _f:
        _f.write(string)


def replace_text_in_file(original_text, final_text, path):
    """Replace original_text with final_text in pathlib: path"""
    path.write_text(path.read_text().replace(original_text, final_text))


def get_tag(repo):
    """Get git.TagReference of repo if it exists, else None.

    returns: git.TagReference object or None
    """
    return next((tag for tag in repo.tags if tag.commit == repo.head.commit), None)


def get_tag_name(repo):
    """Get tag name of repo if it exists, else None.

    returns: String or None
    """
    tag = next((tag for tag in repo.tags if tag.commit == repo.head.commit), None)
    if tag:
        return tag.name
    return None


def git_pull_change(repo, ref):
    """Pull the repo and detect if current position was changed

    return: state string: [changed, unchanged, invalid]
    """
    current = repo.head.commit

    # You can't update a tag, try main or master.
    if ref_is_tag(repo, ref):
        if "main" in repo.remotes.origin.refs:
            repo.git.checkout("main")
        elif "master" in repo.remotes.origin.refs:
            repo.git.checkout("master")
        else:
            LOG.warning("Unable to find main or master in : %s", repo)

    repo.remotes.origin.pull()
    repo_name = repo.working_dir.split("/")[-1]

    try:
        repo.git.checkout(ref)
    except GitCommandError as ex:
        LOG.warning("Git reference %s invalid for %s: %s", ref, repo_name, ex)
        return "invalid"

    if current == repo.head.commit:
        LOG.debug("Git state unchanged: %s", repo_name)
        return "unchanged"

    LOG.debug("Git state changed: %s", repo_name)
    return "changed"


def ref_is_tag(repo, ref):
    """Is this ref a tag?"""
    if ref in repo.tags:
        return True
    return False


def ref_is_branch(repo, ref):
    """Is this ref a tag?"""
    if ref in repo.branches:
        return True
    return False


def ref_is_commit(repo, ref):
    """Is this ref a tag?"""

    # First test if ref is a branch or tag:
    if ref in repo.references:
        return False

    try:
        _ = repo.commit(ref)
    except BadName:
        return False
    else:
        return True


def get_repo_ref_type(repo, ref):
    """Return the reference type as RefType, if possible, else RefType.UNKNOWN"""

    if ref_is_branch(repo, ref):
        return RefType.BRANCH
    if ref_is_tag(repo, ref):
        return RefType.TAG
    if ref_is_commit(repo, ref):
        return RefType.COMMIT

    return RefType.UNKNOWN


def get_repo_ref_state_ok(repo, ref):
    """Determine if state of repo is ok"""
    ref_type = get_repo_ref_type(repo, ref)

    if ref_type.name == "BRANCH":
        if ref in repo.active_branch.name and "is up to date" in repo.git.status():
            return True
    elif ref_type.name == "TAG":
        if ref in repo.git.status():
            return True
    elif ref_type.name == "COMMIT":
        if ref in repo.commit().hexsha:
            return True

    return False


# Pathlib missing features
def rm_tree(path):
    """Remove a pathlib tree

    path: a pathlib.Path object
    returns: boolean True if success.
    """
    if not path.exists():
        LOG.warning("Path does not exist: %s", path)
        return False

    if path.is_file():
        path.unlink()
    else:
        for child in path.iterdir():
            rm_tree(child)
        path.rmdir()
    return True
