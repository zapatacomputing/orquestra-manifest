Introduction: Morq from Orq
==============================

This project attempts to bring order to a large set of Git repositories that together
form a coherent product. The challenge is that simply stitching everything together with
repos in the "main" or "master" state does not guarantee a viable state for a product.

We are then left with dealing with either 1) tagged versions of a branch or worse, 2)
commits of a branch. We prefer the former, as tags are much easier to understand and manage.

Lets proceed: We start by introducing a tool called *Morq*.
It requires a manifest file in JSON format which we describe below.
Morq must have the following base abilities:

#. List the manifest: *list*
#. Download arbitrary git repos: *init*
#. Verify that the repos are in their proper state: *check*
#. Update those repos to a proper git state: *update*
#. Remove all the target repos: *purge*

In addition to the above Morq must be able to do limited installation and testing:

#. Build all the target repos: *build*
#. Test all the target repos: *test*


Why not just use some other tool?
----------------------------------

* Leverage the modern GitPython and Pathlib, instead of ancient 2.7-ish code.
* We want a simple tool that is easy to understand.
* We want to use a JSON format for manifest.json (No XML please ;)
* We want simple tests

Morq Commands
==============
In order to achieve these conditions, we implement these in a simple Command Line
Interface (CLI), which we will outline below. The command we use to invoke these options
will be called *morq*:

List Repo
-------------

This just lists what the manifest believes is truth::

   morq [-m /path/to/manifest.json] list

   +---------------------------------------------------+-------+
   | git@github.com:zapatacomputing/orquestra-auth.git | main  |
   | git@github.com:zapatacomputing/call-simulator.git | 1.0.0 |
   | git@github.com:zapatacomputing/orquestra-sdk.git  | dev   |
   | git@github.com:zapatacomputing/orquestra-foo.git  | dev   |
   +---------------------------------------------------+-------+

Initialize Repos
-----------------
We want to download the repos to some folder and have them checkout to the proper Git
reference, whatever that may be. We do so in this way::

   morq [-m /path/to/some/manifest.json] init

Omitting the -m stuff will assume that you are in the folder that already has a manifest
file. You'll see something like this when invoked::

   INFO:orquestra_manifest.morq:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/orquestra-auth
   INFO:orquestra_manifest.morq:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/call-simulator
   INFO:orquestra_manifest.morq:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/orquestra-sdk
   INFO:orquestra_manifest.morq:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/orquestra-foo
   CRITICAL:orquestra_manifest.morq:  => URL git@github.com:zapatacomputing/orquestra-foo.git does not exist!


Check Repo States
-------------------
Check the repo state and report.::

   morq [-m /path/to/manifest.json] check

Which should produce output similar to::

   +----------------+---------+-------+----------+
   | Folder         | Status  | Ref   | Position |
   +----------------+---------+-------+----------+
   | orquestra-auth | OK      | main  | main     |
   | call-simulator | OK      | 1.0.0 | 1.0.0    |
   | orquestra-sdk  | OK      | dev   | dev      |
   | orquestra-foo  | Missing | dev   | None     |
   +----------------+---------+-------+----------+

Update Repos
-----------------------------------
Update installs or updates repos to their manifest-specified states, be that branch,
tag, commit. Invocation is::

   morq [-m /path/to/manifest.json] update


Purge Installed Repos
-----------------------
Remove all the repos that were installed. *Hulk Smash Repo*
::

   morq [-m /path/to/manifest.json] purge

Status
--------

* Proof of concept is functional for (list, init, update, check, purge).
* Unit tests exist for most major methods.

Remaining Work
---------------
* Improve some methods to make more robust
* Add more tests
* Improved textual output: coloration etc...
* Output information in JSON for devops and automation?

SuperRepo Setup: A Valid Version of the software.
==================================================

A valid version of the software, according to *Morq*, is a manifest.json file
that reflects a collection of repositories that are compatible.
This could be the entire orquestra suite or just a few repos you want to work with.

The ideal for your project should be a tiny Git repo that contains a valid manifest.json.
The project (orquestra-release for example) could have a structure as follows:

::

      .
      +-- README.rst
      +-- docs
      |   `-- index.rst (optional)
       `-- repos
           `-- manifest.json

The manifest.json file is a JSON file of the format::

   {
      "version": "1.1.0",
      "repos": {
         "orquestra-auth": {
            "url": "git@github.com:zapatacomputing/orquestra-auth.git",
            "ref": "2.3.0",
            "type": "python",
            "autodoc": ["orquestra"]
         },
         "orquestra-sdk": {
            "url": "git@github.com:zapatacomputing/orquestra-sdk.git",
            "ref": "1.2.0",
            "type": "python",
            "autodoc": ["src/callsimulator", "automation"]
         },
         ... etc ...
      }
   }

The JSON format must include:

* The 'repos' section that contains  the individual project data.
* The repo mapping is labeled by the repo folder name.
* The 'ref' can be a (tag, branch, commit), but would normally be a *tag* for a release.
* The 'autodoc' line is a list of source modules that are to be indexed by Sphinx.

.. Note::

   * Dependencies: Repos must be listed in dependency order, least to most dependent.
     Morq will build them in the order it sees in the manifest, and will fail if a
     manifest dependency is missing.

   * Every time a sub-repo is updated and tagged, we must update the project manifest.json file.

   * The SuperRepo can have multiple branches corresponding to various features. Promoting those
     features to main is equivalent to a *release*.

   * You must create a Git tag that reflect the correct state of your project as
     defined by this manifest.


SubRepo Setup
====================

Each sub-repo can be *any* Git repo with the following characteristics:

* A Makefile with the following targets:

   #. build   (to build the package)
   #. develop (to build the package for testing)
   #. test    (to test the package)


.. Note:: Requirements:

   * The repo must contain the reference (tag, branch, commit) stated in the manifest.
   * The *make build* target must completely build the package for production use.
   * The *make develop* target must build the package for development and to pass unit tests.

Global Documentation
=====================
As part of this POC we attempt to show that a global documentation scheme is possible in
conjunction with the morq tools above.

Assumptions:

* Each repo has a `~/docs` folder with an `index.rst` per normal Sphinx-doc setup.
* The manifest has a document *autodoc* folder that the *autoapi* tool uses
* Nearly all configuration can be done automatically with enough reasonable effort.

Automatic documentation of Code
--------------------------------
We use Autoapi: https://github.com/readthedocs/sphinx-autoapi because it does not require
that we install the module to document the source. In contrast, Sphinx
autodoc https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html requires you
to install every package in Python.

Autoapi has these useful features:

* Autoapi can document uninstalled code
* Autoapi has support for both Python and Golang

What Works
------------------------------

* Sphinx can be initialized programmatically within a repo folder
* Sphinx configuration can be modified automatically to add *autoapi* features
* Docs in `~/docs` render correctly
* Source documentation listed in the manifest renders decently.

What Needs Development
------------------------------

* All repos must include `~/docs/index.rst` files to make this work.
* Source code RST docs must be implemented.
* Better tests.
* Improve Sphinx theme.
* Refine the *autoapi* output, clean up junk.
* Autoapi only allows one language at this time. Want: Python+Go
* Remove version number from manifest.json, its redundant.
* Remove init, and use update only.. It works. ;)
* Be able to use manifest to install python packages
* Don't invent another Conda. Keep it simple.


Copyright Management
=====================

The copyright tool will automatically add and update copyright notices.

Process
---------

For each branch in the manifest:

* Create a new branch labeled by ticket
* Update copyright if it exists
* Update copyright if none exists
* Commit those changes
* Push those changes up to Github
* A note is printed informing the user to create a PR

Features
----------

* Leverages manifest.json and Morq
* Uses the Git log to identify first-year and last-year for copyright.
* If only one year is detected, use only that year in the copyright.
* Files that already have a copyright are updated.
* Identify files by extension and adds python-style copyright to (".py", "Makefile") and
  c-style copyright to (".go", ".h", ".c", ".cc", ".hpp", ".cpp")
* New branches are:

  - created based on *--ticket=\'ORQSDK-123\'*

  - changed
  - committed, and
  - pushed to origin


Function
---------

To add/update copyrights to files of
you must take these steps:

#. create an empty folder with manifest.json::

      mkdir repos; cd repos
      touch manifest.json

#. Populate manifest.json with the repos and initial branches.
   Ensure that the repo references that branches you want to modify.

#. Initialize all repos::

      morq init

#. Use the copyright tool::

      copyright --ticket='ORQSDK-1234'

#. Go to github.com and create a pull request

