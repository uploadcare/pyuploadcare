=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

.. image:: https://travis-ci.org/uploadcare/pyuploadcare.png?branch=master
   :target: https://travis-ci.org/uploadcare/pyuploadcare

The most important thing for us at `Uploadcare`_ is to make file uploading on
the web really easy. Everyone is used to the routine work, related to allowing
users upload their userpics or attach resumes: from installing image processing
libraries to creating folder with right permissions to ensuring the server
never goes down or out of space to enabling CDN. Feature like ability to simply
use a picture from Facebook or manual cropping are much more burdensome,
hence rare. Uploadcare's goal is to change the status quo.

This library consists of an API interface for `Uploadcare`_ and a couple
of Django goodies.

A simple Uploadcare ``ImageField`` can be added to an existing Django project
in just a couple of `simple steps`_. As a result, your users
are going to be able to see the progress of the upload, choose files from
Google Drive or Instagram, and edit form while files are uploading
asynchornously.

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj import ImageField


    class Candidate(models.Model):

        photo = ImageField(blank=True, manual_crop="")

.. image:: http://www.ucarecdn.com/93b254a3-8c7a-4533-8c01-a946449196cb/-/resize/800/manual_crop.png

Features
--------

- Python wrapper for Uploadcare [REST](https://uploadcare.com/documentation/rest/)
  and [Upload](https://uploadcare.com/documentation/upload/) APIs
- Django widget with useful manual crop and multiupload;
- *ucare* console utility;
- hosted assets (Kudos to `Sławek Ehlert`_!).

Installation
------------

To install it, just run:

.. code-block:: console

    $ pip install pyuploadcare

or, if you're into vintage:

.. code-block:: console

    $ easy_install pyuploadcare

Testing
-------

Besides the `Travis CI`_ we use tox. In order to run tests just:

.. code-block:: console

    $ pip install tox
    $ tox

.. _Uploadcare: https://uploadcare.com/
.. _simple steps: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
.. _Sławek Ehlert: https://github.com/slafs
.. _Travis CI: https://travis-ci.org/uploadcare/pyuploadcare
