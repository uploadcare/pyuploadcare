=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

.. image:: https://travis-ci.org/uploadcare/pyuploadcare.png?branch=master
   :target: https://travis-ci.org/uploadcare/pyuploadcare
   :alt: Build Status
.. image:: https://readthedocs.org/projects/pyuploadcare/badge/?version=latest
   :target: https://readthedocs.org/projects/pyuploadcare/?badge=latest
   :alt: Documentation Status
.. image:: https://coveralls.io/repos/github/uploadcare/pyuploadcare/badge.svg?branch=master
   :target: https://coveralls.io/github/uploadcare/pyuploadcare?branch=master
   :alt: Coverage
.. image:: https://landscape.io/github/uploadcare/pyuploadcare/master/landscape.svg?style=flat
   :target: https://landscape.io/github/uploadcare/pyuploadcare/master
   :alt: Code Health

Simple file uploads for the web are of most importance
for us at `Uploadcare`_. Today, everyone is used to the routine of
allowing users to upload their pics or attach resumes. The routine
covers it all: installing image processing libraries, adjusting permissions,
ensuring servers never go down, and enabling CDN.
Features like uploading from Facebook or manual crop are weighty,
hence rare.
Our goal is to change the status quo.

This library consists of the `Uploadcare`_ API interface and a couple
of Django goodies.

Simple as that, Uploadcare ``ImageField`` can be added to an
existing Django project in just a couple of `simple steps`_.
This will enable your users to see the upload progress, pick files
from Google Drive or Instagram, and edit a form while files are
being uploaded asynchronously.

.. code-block:: python

    from django import forms
    from django.db import models

    from pyuploadcare.dj.models import ImageField
    from pyuploadcare.dj.forms import FileWidget


    class Candidate(models.Model):
        photo = ImageField(blank=True, manual_crop="")


    # optional. provide advanced widget options: https://uploadcare.com/documentation/widget/#configuration
    class CandidateForm(forms.Form):
        photo = ImageField(widget=FileWidget(attrs={
            'data-cdn-base': 'https://cdn.super-candidates.com',
            'data-image-shrink': '1024x1024',
        }))

.. image:: https://ucarecdn.com/dbb4021e-b20e-40fa-907b-3da0a4f8ed70/-/resize/800/manual_crop.png

Features
--------

- Python wrapper for Uploadcare `REST`_ and `Upload`_ APIs.
- Django widget with useful manual crop and multi-upload.
- *ucare* console utility.
- hosted assets (Kudos to `Sławek Ehlert`_!).

Requirements
------------

``pyuploadcare`` requires Python 2.7, 3.4, 3.5 or 3.6.

If you're using ``pyuploadcare`` with Django, check ``.travis.yml`` for supported
Python-Django combinations.

Obsolete versions of Python and Django are officially not supported, but chances
are everything still works. If you have to use those, modify tox.ini, test and
run at your own risk ;) Or, you may use older versions of the library.

Installation
------------

In order to install ``pyuploadcare``, simply run:

.. code-block:: console

    $ pip install pyuploadcare

or, if you prefer it the old way:

.. code-block:: console

    $ easy_install pyuploadcare

Testing
-------

Besides the `Travis CI`_ we use tox. In order to run tests just:

.. code-block:: console

    $ pip install tox
    $ tox

Contributors
------------

- `@marselester`_
- `@dmitry-mukhin`_
- `@zerc`_
- `@homm`_
- `@va1en0k`_
- `@andreshkovskii`_

.. _Uploadcare: https://uploadcare.com/
.. _simple steps: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
.. _Sławek Ehlert: https://github.com/slafs
.. _Travis CI: https://travis-ci.org/uploadcare/pyuploadcare
.. _REST: https://uploadcare.com/documentation/rest/
.. _Upload: https://uploadcare.com/documentation/upload/
.. _@marselester: https://github.com/marselester
.. _@dmitry-mukhin: https://github.com/dmitry-mukhin
.. _@zerc: https://github.com/zerc
.. _@homm: https://github.com/homm
.. _@va1en0k: https://github.com/va1en0k
.. _@andreshkovskii: https://github.com/andrewshkovskii/
