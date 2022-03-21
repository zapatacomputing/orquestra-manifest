"""Common Tools for Orquestra-Manifest"""

import argparse
import json
import logging
import pathlib
import sys
import textwrap

import argcomplete
import git
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from orquestra_manifest.sphinx_tools import install_sphinx, update_sphinx_conf
from orquestra_manifest.tabler import Tabler
from orquestra_manifest.utils import (
    folder_cmd,
    get_repo_ref_state_ok,
    get_repo_ref_type,
    git_pull_change,
    rm_tree,
)

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("orquestra_manifest.common")


class Manifest:
    """Manifest class to manage package groups"""

    def __init__(self):
        self.manifest_file = None

    def parse_args(self):
        """Create the parser for the class"""

        default_manifest_file = "manifest.json"
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(
                r"""
                 __  __                 _
                |  \/  | ___  _ __ __ _| |
                | |\/| |/ _ \| '__/ _` | |
                | |  | | (_) | | | (_| |_|
                |_|  |_|\___/|_|  \__, (_)
                                     |_|
        A Tool to manage SuperRepos defined by manifest.json"""
            ),
        )
        parser.add_argument(
            "-m",
            "--manifest_file",
            default=default_manifest_file,
            help="Alternative location of the manifest file",
        )

        subparsers = parser.add_subparsers()

        parser_init = subparsers.add_parser("init")
        parser_init.set_defaults(func=self.update_repos)

        parser_build = subparsers.add_parser("build")
        parser_build.set_defaults(func=self.build_repos)

        parser_build = subparsers.add_parser("test")
        parser_build.set_defaults(func=self.test_repos)

        parser_check = subparsers.add_parser("check")
        parser_check.set_defaults(func=self.check_repos)

        parser_list = subparsers.add_parser("list")
        parser_list.set_defaults(func=self.list_repos)

        parser_purge = subparsers.add_parser("purge")
        parser_purge.set_defaults(func=self.purge_repos)

        parser_update = subparsers.add_parser("update")
        parser_update.set_defaults(func=self.update_repos)

        parser_sphinx = subparsers.add_parser("sphinx")
        parser_sphinx.set_defaults(func=self.init_sphinx)

        argcomplete.autocomplete(parser)
        args = parser.parse_args(sys.argv[1:])

        # Set/Locate the manifest file.
        if pathlib.Path(args.manifest_file).exists():
            self.manifest_file = pathlib.Path(args.manifest_file).resolve()
        else:
            LOG.critical(
                "No such manifest: %s"
                "\n"
                "\nNote:: "
                "\n\t+-------------------------------------------------------------+"
                "\n\t| You must either be in a folder that contains manifest.json, |"
                "\n\t|  -or- point to the manifest with '-m path/to/manifest.json' |"
                "\n\t+-------------------------------------------------------------+"
                "\n",
                args.manifest_file,
            )
            sys.exit(1)

        try:
            args.func()
        except AttributeError:
            parser.print_help()
            parser.exit()
        else:
            return True

        return False

    def get_manifest(self):
        """Get Manifest dictionary from manifest.json"""

        manifest_fd = self.manifest_file.open(mode="r", encoding="utf-8")
        return json.load(manifest_fd)

    def get_folder_path(self, repo_name):
        """Return the pathlib path to the folder corresponding to repo_name"""
        base_path = self.manifest_file.resolve().parent
        path = base_path / repo_name
        return path

    @staticmethod
    def get_commits_behind_or_ahead(repo, ref):
        """Get number of commits behind or ahead

        Returns:
          * negative integer for behind count
          * positive integer for ahead count
        """

        behind = -1 * sum(1 for x in repo.iter_commits(".." + ref))
        if behind:
            return behind

        ahead = sum(1 for x in repo.iter_commits(ref + ".."))
        if ahead:
            return ahead

        return 0

    def check_repos(self):
        """Check all repos:

        * Report on out-of-sync repos if possible.
        """
        repos = self.get_repos_from_manifest()
        tabler = Tabler()

        # Iterate through all Git folders and try to initialize them in a simple way.
        for repo_name, record in repos.items():
            folder_path = self.get_folder_path(repo_name)
            ref = record.get("ref")
            repo = self.get_valid_repo(folder_path)
            if not repo:
                # Log missing repo.
                LOG.debug("Missing repo %s", folder_path)
                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position="None",
                        status="Missing",
                    )
                )
                continue

            # Repo ref is invalid, skip:
            if ref not in repo.refs:
                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position="invalid",
                        status="invalid",
                    )
                )
                continue

            # If a Git repo is in good status, don't do anything...
            state_ok = get_repo_ref_state_ok(repo, ref)
            if state_ok:
                tabler.push_datum(
                    dict(folder=folder_path.name, ref=ref, position=ref, status="OK")
                )
                continue

            # All else is either behind or ahead. Find out.
            commit_delta = self.get_commits_behind_or_ahead(repo, ref)
            if commit_delta:
                if commit_delta < 0:
                    status = f"{commit_delta} behind"
                else:
                    status = f"{commit_delta} ahead"

                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position=repo.commit().hexsha[:8],
                        status=status,
                    )
                )
                continue

            if repo.is_dirty():
                ref_type = get_repo_ref_type(repo, ref)

                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        ref_type=ref_type.name,
                        status="Dirty",
                    )
                )
        print(tabler.get_table())

    def purge_repos(self):
        """Purge (delete) all repos found in folder_path:

        * Warning: very destructive :)
        """
        repos = self.get_repos_from_manifest()

        # Iterate through all Git folders and delete.
        for repo_name in repos.keys():
            folder_path = self.get_folder_path(repo_name)
            if folder_path.exists():
                rm_tree(folder_path)

    def update_repos(self):
        """Update (delete) all repos found in manifest:

        * Warning: will overwrite temporary work.
        * Do not update the manifest automatically. You should do it externally.
        """
        repos = self.get_repos_from_manifest()
        tabler = Tabler()

        # Iterate through all Git folders and try to initialize them in a simple way.
        for repo_name, record in repos.items():
            folder_path = self.get_folder_path(repo_name)
            ref = record.get("ref")
            repo = self.get_valid_repo(folder_path)
            if not repo:
                # Log missing repo.
                LOG.warning(
                    "Missing repo %s" "\n\t=> Attempting to clone....", folder_path
                )
                # Clone the repo, because its missing
                LOG.info("Cloning repo %s", folder_path)
                url = record.get("url")
                try:
                    repo = git.Repo.clone_from(url, folder_path)
                except GitCommandError as ex:
                    LOG.critical("  => URL %s does not exist!", url)
                    LOG.debug("Full URL error: %s", ex)
                    tabler.push_datum(
                        dict(
                            folder=folder_path.name,
                            ref=ref,
                            position="Invalid",
                            status="Invalid",
                            update="N/A",
                        )
                    )
                    continue

                # You cloned the repo, now checkout the reference.
                try:
                    repo.git.checkout(ref)
                except GitCommandError as ex:
                    LOG.critical("  => Git Ref %s does not exist!: %s", ref, ex)
                    LOG.debug("Full Ref error: %s", ex)
                    tabler.push_datum(
                        dict(
                            folder=folder_path.name,
                            ref=ref,
                            position="Invalid",
                            status="Invalid",
                            update="New",
                        )
                    )
                    continue
                else:
                    tabler.push_datum(
                        dict(
                            folder=folder_path.name,
                            ref=ref,
                            position=ref,
                            status="OK",
                            update="New",
                        )
                    )
                    continue

            # Check that the ref exists here first
            if ref not in repo.refs:
                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position="invalid",
                        status="invalid",
                        update="N/A",
                    )
                )
                continue

            update_status = git_pull_change(repo, ref)
            if update_status == "invalid":
                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position=ref,
                        status="invalid",
                        update=update_status,
                    )
                )
                continue

            # If a Git repo is in good status, check for changes
            state_ok = get_repo_ref_state_ok(repo, ref)
            if state_ok:
                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position=ref,
                        status="OK",
                        update=update_status,
                    )
                )
                continue

            # All else is either behind or ahead. Find out.
            commit_delta = self.get_commits_behind_or_ahead(repo, ref)
            if commit_delta:
                if commit_delta < 0:
                    status = f"{commit_delta} behind"
                else:
                    status = f"{commit_delta} ahead"

                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        position=repo.commit().hexsha[:8],
                        status=status,
                        update=update_status,
                    )
                )
                continue

            if repo.is_dirty():
                ref_type = get_repo_ref_type(repo, ref)
                tabler.push_datum(
                    dict(
                        folder=folder_path.name,
                        ref=ref,
                        ref_type=ref_type.name,
                        status="Dirty",
                        update=update_status,
                    )
                )

        print(tabler.get_table())

    def get_repos_from_manifest(self):
        """Get repos and refs for each manifest repo"""
        manifest = self.get_manifest()
        return manifest.get("repos")

    @staticmethod
    def get_current_branch(repo):
        """Get the current tag if it exists, else None"""
        branch = repo.active_branch.name
        return branch

    @staticmethod
    def get_current_tag(repo):
        """Get the current tag if it exists, else None"""
        tag = next(
            (tag.name for tag in repo.tags if tag.commit == repo.head.commit), None
        )
        return tag

    @staticmethod
    def get_valid_repo(folder_name):
        """For input folder_name, is it a valid repo?

        Return: repo, else None

        """
        repo = None
        try:
            repo = git.Repo(folder_name)
        except NoSuchPathError:
            LOG.debug("Missing Repo Folder : %s", folder_name)
        except InvalidGitRepositoryError:
            LOG.debug("Folder Path is not a git repo: %s", folder_name)
        except Exception as ex:
            LOG.debug("Folder Path unknown error: %s", ex)

        return repo

    def build_repos(self):
        """Build all repos

        Return: (int) Total error
        """
        total_error = 0
        error = 0
        tabler = Tabler()
        repos = self.get_repos_from_manifest()
        make_cmd = ["make", "install"]
        pip_cmd = ["python3", "-m", "pip", "install", "."]

        for _folder, _record in repos.items():
            folder_path = self.get_folder_path(_folder)
            make_path = folder_path / "Makefile"

            if make_path.exists():
                error = folder_cmd(folder_path, make_cmd)
                state = "Failed" if error else "OK"

            elif _record.get("type") == "python":
                error = folder_cmd(folder_path, pip_cmd)
                state = "Failed" if error else "OK"

            else:
                error = 10
                state = f"Builder {_folder} N/A"

            total_error += error
            tabler.push_datum(dict(folder=_folder, build=state))

        print(tabler.get_table())
        return total_error

    def test_repos(self):
        """Test all repos

        Return: Total error
        """
        total_error = 0
        tabler = Tabler()
        repos = self.get_repos_from_manifest()

        for _folder, _ in repos.items():
            error = 0
            folder_path = self.get_folder_path(_folder)
            error += folder_cmd(folder_path, ["make", "develop"], stdout=False)
            error += folder_cmd(folder_path, ["make", "test"], stdout=True)
            total_error += error
            tabler.push_datum(dict(folder=_folder, test=("Failed" if error else "OK")))

        print(tabler.get_table())
        return total_error

    def list_repos(self):
        """List repos and refs for each manifest repo"""
        repos = self.get_repos_from_manifest()
        tabler = Tabler()

        for _, record in repos.items():
            tabler.push_datum(dict(url=record.get("url"), ref=record.get("ref")))
        print(tabler.get_table())

    def init_sphinx(self):
        """Initialize and setup Sphinx for the manifest path"""
        self.update_repos()
        base_path = self.manifest_file.resolve().parent
        install_sphinx(base_path)
        update_sphinx_conf(self)


def morq_cli():
    """Main function that parses and executes all other commands"""
    LOG.debug("Using morq_cli")

    try:
        manifest = Manifest()
        manifest.parse_args()

    except KeyboardInterrupt:
        sys.exit(1)

    except AttributeError as ex:
        raise AttributeError from ex

    except Exception as ex:
        raise Exception from ex


if __name__ == "__main__":
    morq_cli()
