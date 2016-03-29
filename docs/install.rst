.. _install:

============
Installation
============

This part of the documentation covers the installation of PyUploadcare.

.. _install-pip-ref:

Pip
---

Installing pyuploadcare is simple with pip:

.. code-block:: console

    $ pip install pyuploadcare

or, if you're into vintage:

.. code-block:: console

    $ easy_install pyuploadcare

.. _install-get-the-code-ref:

Get the Code
------------

PyUploadcare is developed on GitHub. You can clone the public repository:

.. code-block:: console

    $ git clone git://github.com/uploadcare/pyuploadcare.git

After that you can install it:

.. code-block:: console

    $ python setup.py install


Update to version 2.0
---------------------

Some caveats about migration process from version 1.x to 2.x.

A version 2.0 contains the next breaking changes:

Changed initializing for the ``FileList`` and ``GroupList`` classes.
The ``since`` and ``until`` parameters has been removed. Use combination from
``starting_point`` and ``ordering`` instead.

The ``ucare list`` CLI command has been renamed to ``ucare list_files``. And
according to the previous change, the ``since`` and ``until`` parameters has
been removed here. The ``starting_point`` and ordering parameters added.

These changes a necessary for working with 0.5 version of REST API.
So that means you can’t use these classes correctly with versions prior 0.5.

Also, note that setting ``UPLOADCARE['widget_variant']`` now is deprecated and
it’s will be removed in next major release. Use ``UPLOADCARE['widget_build']``
instead.
