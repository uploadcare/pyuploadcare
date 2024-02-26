=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

Uploadcare Python & Django integrations handle uploads and further operations
with files by wrapping Upload and REST APIs.

Simple file uploads for the web are of most importance for us. Today, everyone
is used to the routine of allowing users to upload their pics or attach resumes.
The routine covers it all: installing image processing libraries, adjusting
permissions, ensuring servers never go down, and enabling CDN.

This library consists of the Uploadcare API interface and a couple of Django
goodies.

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
    from pyuploadcare.dj.forms import FileWidget, ImageField as ImageFormField


    class Candidate(models.Model):
        photo = ImageField(blank=True, manual_crop='4:3')


    # Optional: provide advanced widget options https://uploadcare.com/docs/file-uploader/options/
    class CandidateForm(forms.Form):
        photo = ImageFormField(widget=FileWidget(attrs={
            "source-list": "local,url,camera",
            "camera-mirror": True,
        }))

.. image:: https://ucarecdn.com/f0894ef2-352e-406a-8279-737dd6e1f10c/-/resize/800/manual_crop.png

Features
========

- Python wrapper for Uploadcare `REST`_ and `Upload`_ APIs.
- Django `widget`_ with useful manual crop and multi-upload.
- *ucare* console utility.

Requirements
============

``pyuploadcare`` requires Python 3.8, 3.9, 3.10, 3.11, 3.12

To use ``pyuploadcare`` with Python 3.6 or 3.7 please install ``pyuploadcare < 5.0``.

To use ``pyuploadcare`` with Python 2.7 please install ``pyuploadcare < 3.0``.

If you're using ``pyuploadcare`` with Django, refer the following compatibility table:

.. csv-table:: Django compatibility
   :header-rows: 1
   :align: center

    Py/Dj,2.2,3.0,3.1,3.2,4.0,4.1,4.2,5.0
    3.8,X,X,X,X,X,X,X,
    3.9,X,X,X,X,X,X,X,
    3.10,,,,X,X,X,X,X
    3.11,,,,,,X,X,X
    3.12,,,,,,,X,X

Contents
========

.. toctree::
   :maxdepth: 2

   install
   quickstart
   django-widget
   core_api
   testing
   security_issues
   feedback

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Uploadcare: https://uploadcare.com
.. _simple steps: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
.. _REST: https://uploadcare.com/api-refs/rest-api/?utm_source=github&utm_campaign=pyuploadcare
.. _Upload: https://uploadcare.com/api-refs/upload-api/?utm_source=github&utm_campaign=pyuploadcare
.. _widget: https://uploadcare.com/docs/uploads/file-uploader/
.. _here: https://github.com/uploadcare/pyuploadcare-example
