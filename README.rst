Orquestra Manifest
====================
Enforce some sense of order to the Orquestra.
We use a simple manifest.json file to specify all the goods.

Find the official project manifest file here::

      repos/manifest.json

The repositories get downloaded in repos/ as well, but in principle, they could be
located anywhere.

* See https://myrepos.branchable.com/ and https://github.com/nosarthur/gita for
  inspiration

You can find more details in `docs/`.

Why not just use some other tool?
----------------------------------
* We want a simple tool that is easy to understand.
* We want to use a JSON format for manifest.json
* We want simple tests
* We want to leveage modern tools like GitPython and Pathlib

Installation
-------------

In order to install `morq` you can just run `make install` from the root directory.