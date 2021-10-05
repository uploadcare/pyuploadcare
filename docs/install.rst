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

    $ pip install .


Update to version 2.0
---------------------

Some caveats about migration process from version 1.x to 2.x.

A version 2.0 contains the next breaking changes:

* Now, you should import Django models' fields (e.g ``ImageField``) directly from the ``pyuploadcare.dj.models`` module.

* Changed initializing for the ``FileList`` and ``GroupList`` classes. The ``since`` and ``until`` parameters have been removed. Use combination of ``starting_point`` and ``ordering`` instead.

* The ``ucare list`` CLI command has been renamed to ``ucare list_files``. And, according to the previous change, the ``since`` and ``until`` parameters have been removed. The ``starting_point`` and ordering parameters added.

These last two changes are necessary for working with version 0.5 of REST API.
So that means you can’t use these classes correctly with versions prior 0.5
(but that should not be an issue :)

Also, note that Django configuration option ``UPLOADCARE['widget_variant']``
now is deprecated and it will be removed in next major release. Use
``UPLOADCARE['widget_build']`` instead.

Update to version 3.0
---------------------

Some caveats about migration process from version 2.x to 3.x.

A version 3.0 contains the next breaking changes:

* Resource attributes can be accessed now as properies, not methods.
  In 2.x version use ``file.is_stored()``, in 3.x verisons use ``file.is_stored``.
