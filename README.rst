=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

.. image:: https://travis-ci.org/uploadcare/pyuploadcare.png?branch=master
   :target: https://travis-ci.org/uploadcare/pyuploadcare
.. image:: https://readthedocs.org/projects/pyuploadcare/badge/?version=latest
   :target: https://readthedocs.org/projects/pyuploadcare/?badge=latest
   :alt: Documentation Status

The most important thing for us at `Uploadcare`_ is to make file uploading on
the web really easy. Everyone is used to the routine work, related to allowing
users upload their user pics or attach resumes: from installing image processing
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
asynchronously.

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

- Python wrapper for Uploadcare `REST`_ and `Upload`_ APIs
- Django widget with useful manual crop and multi-upload;
- *ucare* console utility;
- hosted assets (Kudos to `Sławek Ehlert`_!).

Requirements
------------

``pyuploadcare`` requires Python 2.6, 2.7, 3.3, 3.4 or 3.5.

If you're using ``pyuploadcare`` with Django, check ``.travis.yml`` for supported
Python-Django combinations.


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
.. _REST: https://uploadcare.com/documentation/rest/
.. _Upload: https://uploadcare.com/documentation/upload/
