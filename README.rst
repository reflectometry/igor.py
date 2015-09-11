Note
====

This package has been superseded by `igor <http://pypi.python.org/pypi/igor>`_. 

Use the new igor package with the following to get the same interface::

    import igor.igorpy as igor

Igor.py
=======

:Author: Paul Kienzle <paul.kienzle@nist.gov>
:License: This program is public domain

Read Igor Pro files from python.

Install
-------

Using pip::

    $ pip install igor.py

Using source, download and expand the source tree, change to the source
directory and type::

    $ python setup.py install

Change History
--------------

0.9.1 2015-09-11

* pypi forced a revision upgrade to update the readme; it won't even allow
  the old 0.9 version to be restored on the site!

0.9  2011-10-14  Merlijn van Deen

* access to data object using f.name in addition to f['name'] and f[i]
* allow a data object to be used directly as an array, e.g., numpy.sum(f.name)
* better unicode handling

0.8  2011-04-27  Paul Kienzle

* initial release

Maintenance
-----------

When a new version of the package is ready, increment __version__
in igor.py and enter::

    $ python setup.py sdist upload

This will place a new version on pypi.

