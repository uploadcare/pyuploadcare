=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

Simple file uploads for the web are of most importance
for us at `Uploadcare`_. Today, everyone is used to the routine of
allowing users to upload their pics or attach resumes. The routine
covers it all: installing image processing libraries, adjusting permissions,
ensuring servers never go down, and enabling CDN.

This library consists of the `Uploadcare`_ API interface and a couple
of Django goodies.

Simple as that, Uploadcare ``ImageField`` can be added to an
existing Django project in just a couple of `simple steps`_.
This will enable your users to see the upload progress, pick files
from Google Drive or Instagram, and edit a form while files are
being uploaded asynchronously.

You can find an example project `here`_.

.. code-block:: python

    from django import forms
    from django.db import models

    from pyuploadcare.dj.models import ImageField
    from pyuploadcare.dj.forms import FileWidget


    class Candidate(models.Model):
        photo = ImageField(blank=True, manual_crop="")


    # optional. provide advanced widget options: https://uploadcare.com/docs/uploads/widget/config/#options
    class CandidateForm(forms.Form):
        photo = ImageField(widget=FileWidget(attrs={
            'data-cdn-base': 'https://cdn.super-candidates.com',
            'data-image-shrink': '1024x1024',
        }))

.. image:: https://ucarecdn.com/dbb4021e-b20e-40fa-907b-3da0a4f8ed70/-/resize/800/manual_crop.png

Features
========

- Python wrapper for Uploadcare `REST`_ and `Upload`_ APIs.
- Django widget with useful manual crop and multi-upload.
- *ucare* console utility.

Requirements
============

``pyuploadcare`` requires Python 3.6, 3.7, 3.8, 3.9.

To use ``pyuploadcare`` with Python 2.7 please install ``pyuploadcare < 3.0``.

If you're using ``pyuploadcare`` with Django, check ``tox.ini`` or
``.github/workflows`` for supported Python-Django combinations.


Contents
========

.. toctree::
   :maxdepth: 2

   install
   quickstart
   django-widget
   cli
   core_usage
   deprecated
   testing
   security_issues
   feedback

API Reference
=============

.. toctree::
   :maxdepth: 2

   api/core
   api/django-widget
   api/cli

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Uploadcare: https://uploadcare.com
.. _simple steps: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
.. _REST: https://uploadcare.com/api-refs/rest-api/?utm_source=github&utm_campaign=pyuploadcare
.. _Upload: https://uploadcare.com/api-refs/upload-api/?utm_source=github&utm_campaign=pyuploadcare
.. _here: https://github.com/uploadcare/pyuploadcare-example
