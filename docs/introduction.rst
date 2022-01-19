Introduction
==============

This project attempts to bring order to a large set of Git repositories that together
form a coherent product. The challenge is that simply stitching everything together with
repos in the "main" or "master" state does not guarantee a viable state for a product.

We are then left with dealing with either 1) tagged versions of a branch or worse, 2)
commits of a branch. We prefer the former, as tags are much easier to understand and manage.

Lets proceed:

We start from a manifest file in JSON format::


   {
      "version": "1.1.0",
      "repos": {
         "orquestra-auth": {
            "url": "git@github.com:zapatacomputing/orquestra-auth.git",
            "ref": "main",
            "type": "python",
            "autodoc": ["orquestra"]
         },
         "call-simulator": {
            "url": "git@github.com:zapatacomputing/call-simulator.git",
            "ref": "1.0.0",
            "type": "python",
            "autodoc": ["src/callsimulator", "automation"]
         },
         ...
      }
   }

We wish for the following conditions with respect to that manifest:

#. Ability to list the manifest: *list*
#. Ability to download arbitrary git repos: *init*
#. Ability to verify that the repos are in their proper state: *check*
#. Maintain those repos in a proper git state: *update*
#. Ability to remove all the target repos: *purge*


We list the basic commands that we associate to those tasks.

Why not just use some other tool?
----------------------------------
* Leverage modern tools like GitPython and Pathlib, instead of older 2.7-ish stuff
* We want a simple tool that is easy to understand.
* We want to use a JSON format for manifest.json (No XML please ;)
* We want simple tests


Repo Mechanics
==============
In order to achieve these 5 conditions, we implement these in a simple Command Line
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

   INFO:orquestra_manifest.common:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/orquestra-auth
   INFO:orquestra_manifest.common:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/call-simulator
   INFO:orquestra_manifest.common:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/orquestra-sdk
   INFO:orquestra_manifest.common:Cloning repo /Users/carinhas/orquestra-manifest/tests/data/orquestra-foo
   CRITICAL:orquestra_manifest.common:  => URL git@github.com:zapatacomputing/orquestra-foo.git does not exist!


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

How to Get to a Valid Version
===============================
1. Checkout this repo
2. Find the tag for the release you are interested in
3. Checkout that tag here.
4. The master manifest.json would now reflect your correct tagged release.


Global Documentation
=====================
As part of this POC we attempt to show that a global documentation scheme is possible in
conjunction with the morq tools above.

Assumptions:

* Each repo has a `~/docs` folder with an `index.rst` with possibly more rst files.
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

* Sphinx can be initialized programatically within a repo folder
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
* Remove verison number from manifest.json, its redundant.
* Remove init, and use update only.. It works. ;)
* Be able to use manifest to install python packages
* Don't invent another Conda... Keep it simple.

