"""Sphinx utils for this package"""
import logging
import os
import pathlib
import sys

from sphinx.cmd import quickstart

from orquestra_manifest.utils import (
    add_line_to_file,
    append_string_to_file,
    replace_text_in_file,
)

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("orquestra_manifest.sphinx_tools")


def install_sphinx(folder, project_name="GenericProject", author="Zapata Computing"):
    """Install Sphinx in this folder

    folder: a pathlib Path
    returns: boolean True if success
    """
    if not folder.is_dir():
        LOG.critical("No such folder exists %s", folder)
        return False

    os.chdir(folder)
    args = ["-q", "--project", project_name, "--author", author]
    LOG.info("Installing a Sphinx configuration to %s", folder)
    quickstart.main(args)

    return True


def update_sphinx_conf(manifest):
    """Update Sphinx $folder/conf.py

    manifest: a orquestra_manifest.common.Manifest object
    return: boolean if success
    """
    _folder = manifest.manifest_file.parent
    if not _folder.is_dir():
        LOG.critical("No such folder exists %s", _folder)
        return False

    os.chdir(_folder)

    # This is to allow us to import conf.py and figure out what is in it.
    sys.path.append(os.getcwd())
    import conf as sphinx_conf  # pylint: disable=E0401,C0415

    # -------------------------------------------------------------------------
    # Add the */docs/index to index.rst
    index_path = pathlib.Path("index.rst")

    add_string = "   :glob:"
    if add_string not in sphinx_conf.extensions:
        match_line = "   :caption: Contents:\n"
        add_line_to_file(f"{add_string}\n", match_line, index_path)
    add_string = "\n   */docs/index"
    if add_string not in sphinx_conf.extensions:
        match_line = "   :glob:\n"
        add_line_to_file(f"{add_string}\n", match_line, index_path)
    # -------------------------------------------------------------------------
    # Add copy -a line to Makefile
    makefile_path = pathlib.Path("Makefile")
    add_string = (
        "\nhtml: Makefile"
        '\n\t@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)'
        "\n\tcp -a _build/html /tmp/"
        "\n"
    )
    append_string_to_file(add_string, makefile_path)

    # -------------------------------------------------------------------------
    conf_path = pathlib.Path("conf.py")
    # Replace the theme of alabaster with sphinx_rtd_theme
    replace_text_in_file("alabaster", "sphinx_rtd_theme", conf_path)

    # Add the autoapi extension to conf.py
    add_string = "autoapi.extension"
    if add_string not in sphinx_conf.extensions:
        match_line = "extensions = ["
        add_line_to_file(f"    '{add_string}',\n", match_line, conf_path)

    # Add the python doc folders into autoapi_dirs
    if not hasattr(sphinx_conf, "autoapi_dirs"):
        match_line = "html_static_path = ['_static']"
        add_line_to_file("\nautoapi_dirs = [\n]\n", match_line, conf_path)

        api_match_line = "autoapi_dirs = ["
        repos = manifest.get_repos_from_manifest()
        for folder, record in repos.items():
            # Skip the bogus folders
            if not pathlib.Path(folder).exists():
                continue
            autodoc = record.get("autodoc")
            for path in autodoc:
                path = folder + "/" + path
                add_line_to_file(f"    '{path}',\n", api_match_line, conf_path)

    # add autoapi adjustments to bottom of conf.py
    strings_to_append_conf = [
        'autoapi_ignore = ["*/tests*", "*/project*", "*/docs/*"]\n',
        'autoapi_root = "api"\n',
    ]
    for line in strings_to_append_conf:
        append_string_to_file(line, conf_path)

    return True
