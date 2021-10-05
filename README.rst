.. image:: https://ucarecdn.com/2f4864b7-ed0e-4411-965b-8148623aa680/-/inline/yes/uploadcare-logo-mark.svg
   :target: https://uploadcare.com/?utm_source=github&utm_campaign=pyuploadcare
   :height: 64 px
   :width: 64 px
   :align: left

=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

.. image:: https://badge.fury.io/py/pyuploadcare.svg
   :target: https://badge.fury.io/py/pyuploadcare
.. image:: https://github.com/uploadcare/pyuploadcare/actions/workflows/test.yml/badge.svg
   :target: https://github.com/uploadcare/pyuploadcare/actions/workflows/test.yml
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
.. image:: https://img.shields.io/badge/tech-stack-0690fa.svg?style=flat
   :target: https://stackshare.io/uploadcare/stacks/
   :alt: Uploadcare tech stack

Simple file uploads for the web are of most importance
for us at `Uploadcare`_. Today, everyone is used to the routine of
allowing users to upload their pics or attach resumes. The routine
covers it all: installing image processing libraries, adjusting permissions,
ensuring servers never go down, and enabling CDN.
Features like uploading from Facebook or manual crop are weighty,
hence rare.
Our goal is to change the status quo.

This library consists of the `Uploadcare`_ API interface and a couple
of Django goodies. You might also want to check out this `guide`_ as
a starting point.

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
- hosted assets (Kudos to `Sławek Ehlert`_!).

Requirements
============

``pyuploadcare`` requires Python 3.6, 3.7, 3.8, 3.9.

To use ``pyuploadcare`` with Python 2.7 please install ``pyuploadcare < 3.0``.

If you're using ``pyuploadcare`` with Django, check ``tox.ini``  or
``.github/workflows``  for supported Python-Django combinations.

Obsolete versions of Python and Django are officially not supported, but chances
are that everything still works. If you have to use those, modify ``tox.ini``,
test and run at your own risk ;) Or, you may use older versions of the library.

Installation
============

In order to install ``pyuploadcare``, simply run:

.. code-block:: console

    $ pip install pyuploadcare

or, if you prefer it the old way:

.. code-block:: console

    $ easy_install pyuploadcare


Usage
=====

Core API
--------

You can use pyuploadcare in any Python project. At first you need assign
your project keys to conf object. After that you will be able
to do direct api calls or use api resources::

    import pyuploadcare
    pyuploadcare.conf.pub_key = '<your public key>'
    pyuploadcare.conf.secret = '<your private key>'

Uploading files
^^^^^^^^^^^^^^^

Upload single file. ``File.upload`` method can accept file object or URL. Depending of file object size
direct or multipart upload method will be chosen::

    with open('file.txt') as file_object:
        ucare_file: File = File.upload(file_object)


Upload file from url::

    ucare_file: File = File.upload("https://github.githubassets.com/images/modules/logos_page/Octocat.png")

Upload multiple files. Direct upload method is used::

    file1 = open('file1.txt')
    file2 = open('file2.txt')
    ucare_files: List[File] = File.upload_files([file1, file2])

Send single file via multipart upload::

    with open('file.txt') as file_object:
        ucare_file: File = File.upload(file_object)

``File.upload`` method accepts optional callback function to track uploading progress.
Example of using callback function for printing progress::

    >>> def print_progress(info: UploadProgress):
    ...     print(f'{info.done}/{info.total} B')

    >>> # multipart upload is used
    >>> with open('big_file.jpg', 'rb') as fh:
    ...    File.upload(fh, callback=print_progress)
    0/11000000 B
    5242880/11000000 B
    10485760/11000000 B
    11000000/11000000 B

    >>> # upload from url is used
    >>> File.upload("https://github.githubassets.com/images/modules/logos_page/Octocat.png", callback=print_progress)
    32590/32590 B

    >>> # direct upload is used. Callback is called just once after successful upload
    >>> with open('small_file.jpg', 'rb') as fh:
    ...     File.upload(fh, callback=print_progress)
    56780/56780 B


Video conversion
^^^^^^^^^^^^^^^^
Uploadcare can encode video files from all popular formats, adjust their quality, format and dimensions, cut out a video fragment, and generate thumbnails via REST API.

After each video file upload you obtain a file identifier in UUID format. Then you can use this file identifier to convert your video in multiple ways::

    file = File('740e1b8c-1ad8-4324-b7ec-112c79d8eac2')
    transformation = (
        VideoTransformation()
            .format(Format.mp4)
            .size(width=640, height=480, resize_mode=ResizeMode.add_padding)
            .quality(Quality.lighter)
            .cut(start_time='2:30.535', length='2:20.0')
            .thumbs(10)
    )
    converted_file: File = file.convert(transformation)

or you can use API directly to convert single or multiple files::

    video_convert_api = api.VideoConvertAPI()
    transformation = VideoTransformation().format(VideoFormat.webm).thumbs(2)
    paths: List[str] = [
        transformation.path("740e1b8c-1ad8-4324-b7ec-112c79d8eac2"),
    ]

    response = video_convert_api.convert(paths)
    video_convert_info = response.result[0]
    converted_file = File(video_convert_info.uuid)

    video_convert_status = video_convert_api.status(video_convert_info.token)

Document Conversion
^^^^^^^^^^^^^^^^^^^
Uploadcare allows converting documents to the following target formats: doc, docx, xls, xlsx, odt, ods, rtf, txt, pdf, jpg, png. Document Conversion works via our REST API.

After each document file upload you obtain a file identifier in UUID format. Then you can use this file identifier to convert your document to a new format::

    file = File('0e1cac48-1296-417f-9e7f-9bf13e330dcf')
    transformation = DocumentTransformation().format(DocumentFormat.pdf)
    converted_file: File = file.convert(transformation)

or create an image of a particular page (if using image format)::

    file = File('5dddafa0-a742-4a51-ac40-ae491201ff97')
    transformation = DocumentTransformation().format(DocumentFormat.png).page(1)
    converted_file: File = file.convert(transformation)

or you can use API directly to convert single or multiple files::

    document_convert_api = api.DocumentConvertAPI()
    transformation = DocumentTransformation().format(DocumentFormat.pdf)

    paths: List[str] = [
        transformation.path("0e1cac48-1296-417f-9e7f-9bf13e330dcf"),
    ]

    response = document_convert_api.convert([path])
    document_convert_info = response.result[0]
    converted_file = File(document_convert_info.uuid)

    document_convert_status = document_convert_api.status(document_convert_info.token)

Testing
=======

Besides the `Github Actions`_ we use tox. In order to run tests just:

.. code-block:: console

    $ pip install tox
    $ tox

Security issues
===============

If you think you ran into something in Uploadcare libraries which might have
security implications, please hit us up at `bugbounty@uploadcare.com`_
or Hackerone.

We'll contact you personally in a short time to fix an issue through co-op and
prior to any public disclosure.

Feedback
========

Issues and PRs are welcome. You can provide your feedback or drop us a support
request at `hello@uploadcare.com`_.

Contributors
============

- `@marselester`_
- `@dmitry-mukhin`_
- `@zerc`_
- `@homm`_
- `@va1en0k`_
- `@andreshkovskii`_



.. _Uploadcare: https://uploadcare.com/?utm_source=github&utm_campaign=pyuploadcare
.. _guide: https://uploadcare.com/docs/guides/django/?utm_source=github&utm_campaign=pyuploadcare
.. _simple steps: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
.. _Sławek Ehlert: https://github.com/slafs
.. _Github Actions: https://github.com/uploadcare/pyuploadcare/actions
.. _REST: https://uploadcare.com/docs/api_reference/rest/?utm_source=github&utm_campaign=pyuploadcare
.. _Upload: https://uploadcare.com/docs/api_reference/upload/?utm_source=github&utm_campaign=pyuploadcare
.. _@marselester: https://github.com/marselester
.. _@dmitry-mukhin: https://github.com/dmitry-mukhin
.. _@zerc: https://github.com/zerc
.. _@homm: https://github.com/homm
.. _@va1en0k: https://github.com/va1en0k
.. _@andreshkovskii: https://github.com/andrewshkovskii/

.. _bugbounty@uploadcare.com: mailto:bugbounty@uploadcare.com
.. _hello@uploadcare.com: mailto:hello@uploadcare.com
