import argparse

# from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
import logging
import re
import os

from orquestra_manifest.morq import Manifest

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("orquestra_manifest.morq")

SCRIPT_RX = re.compile(r"(?P<firstline>^#!.*?$)", re.M)
FILE_RX = re.compile(r"(?P<firstline>^.*?$)", re.M)
COPYRIGHT_RX = re.compile(
    r"(?P<copyright>\s*?[\u00a9] Copyright \d{4}(-\d{4})? Zapata Computing Inc.).*"
)


def write_file(file, text):
    with open(file, "w") as fp:
        fp.write(text)


def make_pythonic_copyright(date_string):
    copyright_lines = (
        "################################################################################\n"
        f"# © Copyright {date_string} Zapata Computing Inc.\n"
        "################################################################################"
    )
    return copyright_lines


def make_cstyle_copyright(date_string):
    copyright_lines = (
        "/*\n"
        "  ------------------------------------------------------------\n"
        f"   © Copyright {date_string} Zapata Computing Inc.\n"
        "  ------------------------------------------------------------\n"
        "*/"
    )
    return copyright_lines


def make_copyright_line(date_string):
    copyright_line = f"© Copyright {date_string} Zapata Computing Inc."
    return copyright_line


def is_script(text):
    if text.startswith("#!"):
        return True
    return False


def add_copyright_to_script(copyright, text):
    # Try to make a decent looking copyright line for scripts.
    match = SCRIPT_RX.search(text)
    new = ""
    if match:
        new = re.sub(SCRIPT_RX, r"\g<firstline>\n" + copyright, text, count=1)
        return new


def add_copyright_to_file(copyright, text):
    # Try to make a decent looking copyright line for scripts.
    if not text:
        return text

    match = FILE_RX.search(text)
    if match:
        new = re.sub(FILE_RX, copyright + r"\n\g<firstline>", text, count=1)
        return new


def insert_copyright(first_year, last_year, file):

    # Read entire file data
    with open(file, "r") as fp:
        file_text = fp.read()

    # No need to copyright an empty file.
    if not file_text:
        return

    # Prepare the year_string line.
    if first_year == last_year:
        year_string = str(first_year)
    else:
        year_string = str(first_year) + "-" + str(last_year)

    # See if there is an existing copyright, prepare a modification.
    copyright_line = make_copyright_line(year_string)
    new_file_text = ""
    match = COPYRIGHT_RX.search(file_text)
    if match:
        found_copyright = match.group("copyright")
        # Update the copyright if needed:
        if str(last_year) not in found_copyright:
            new_file_text = re.sub(COPYRIGHT_RX, copyright_line, file_text)
            write_file(file, new_file_text)
        return

    # -------------------------------------------------------------------------
    # Everthing below here has no Copyright.
    # -------------------------------------------------------------------------

    # Now deal with scripts. They start with #! type of operators:
    if is_script(file_text):
        copyright = make_pythonic_copyright(year_string)
        new_file_text = add_copyright_to_script(copyright, file_text)
        if new_file_text:
            write_file(file, new_file_text)
        else:
            LOG.debug("Missing new_file_text for script")
        return

    # The remainder are Python modules or other. Deal with accordingly.
    if file.endswith((".go", ".h", ".c", ".cc", ".hpp", ".cpp")):
        copyright = make_cstyle_copyright(year_string)
    else:
        copyright = make_pythonic_copyright(year_string)

    match = FILE_RX.search(file_text)
    if match:
        new_file_text = add_copyright_to_file(copyright, file_text)
        write_file(file, new_file_text)


def folder_walk(repo, command):
    """Execute cmd on pathlib.Path folder"""
    extension = (".py", "Makefile", ".go", ".h", ".c", ".cc", ".hpp", ".cpp")
    for dirpath, dnames, fnames in os.walk(repo.working_dir):
        for file in fnames:
            if file.endswith(extension):
                path = os.path.join(dirpath, file)
                commits = list(repo.iter_commits(paths=path))
                first_year = commits[-1].committed_datetime.year
                last_year = commits[0].committed_datetime.year
                command(first_year, last_year, path)


def copy_brand(ticket=None):

    manifest = Manifest("manifest.json")
    repos = manifest.get_repos_from_manifest()
    for repo_name, record in repos.items():
        folder_path = manifest.get_folder_path(repo_name)
        repo = manifest.get_valid_repo(folder_path)
        if not repo:
            # Log missing repo.
            LOG.error("Missing repo %s", folder_path)
            continue

        if ticket in repo.refs:
            repo.git.checkout(ticket)
        else:
            repo.git.checkout("-b", ticket)

        folder_walk(
            repo,
            insert_copyright,
        )
        repo.git.add(update=True)
        commit_message = f"Add Copyright for ticket: {ticket}"
        repo.index.commit(commit_message)
        repo.git.push()
        LOG.info("Repo %s.%s has is ready for a PR", folder_path.stem, ticket)


def copyright():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ticket", dest="ticket", type=str, help="ticket to label the branch"
    )
    args = parser.parse_args()
    ticket = args.ticket
    copy_brand(ticket=ticket)
