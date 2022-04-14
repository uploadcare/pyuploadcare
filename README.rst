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
.. image:: https://img.shields.io/badge/tech-stack-0690fa.svg?style=flat
   :target: https://stackshare.io/uploadcare/stacks/
   :alt: Uploadcare tech stack


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

.. contents:: **Table of Contents**

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

Installation
============

This part of the documentation covers the installation of PyUploadcare.

Pip
---

In order to install ``pyuploadcare``, simply run:

.. code-block:: console

    $ pip install pyuploadcare

or, if you prefer it the old way:

.. code-block:: console

    $ easy_install pyuploadcare

To use in Django project install with extra dependencies:

.. code-block:: console

    $ pip install pyuploadcare[django]

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

* ``Uploadcare`` client should be initialized to access API.
  Refer to the documentation to see examples of using ``Uploadcare`` client::

    uploadcare = Uploadcare(
        public_key='<your public key>',
        secret_key='<your private key>',
    )


* ``File``, ``FileGroup``, ``FileList`` and ``GroupList`` resources cannot be initialized directly.
  ``uploadcare.file``, ``uploadcare.file_group``, ``uploadcare.list_files``, ``uploadcare.list_file_groups``
  client methods should be used instead::

    file: File = uploadcare.file('a771f854-c2cb-408a-8c36-71af77811f3b')
    file_group: FileGroup = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
    file_groups: GroupList = uploadcare.list_file_groups()
    files: FileList = uploadcare.list_files(stored=True)

* ``pyuploadcare.conf`` package still can be used for configuration, but it is more preferable to pass
  configuration options to ``Uploadcare`` client on initialization. ``pyuploadcare.conf`` provides
  default values for the client.

Quickstart
==========

This page gives a good introduction in how to get started with PyUploadcare.
This assumes you have already installed PyUploadcare. If you do not,
head over to the :ref:`Installation <install>` section.

.. warning:: Keep in mind that Uploadcare signature authentication will fail
   if computer clock is not synchronized.

Get API Keys
------------

First of all, you'll need API keys: public and private. You can get them
at the `Uploadcare`_ website. If you don't have an account yet, you can use
demo keys, as in example. However, the files on demo account are regularly
deleted, so create an account as soon as Uploadcare catches your fancy.

How to use it with Django?
--------------------------

Assume you have a Django project with *gallery* app.

Application Setup
~~~~~~~~~~~~~~~~~

Add ``pyuploadcare.dj`` into ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...
        'pyuploadcare.dj',

        'gallery',
    )

As soon as you :ref:`got your API keys <quickstart-api-keys-ref>`, add them
to your Django settings file:

.. code-block:: python

    UPLOADCARE = {
        'pub_key': 'demopublickey',
        'secret': 'demoprivatekey',
    }

Uploadcare image field adding to your ``gallery/models.py`` is really simple.
Like that:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import ImageField


    class Photo(models.Model):

        title = models.CharField(max_length=255)
        photo = ImageField()

``ImageField`` doesn't require any arguments, file paths or whatever.
**It just works.** That's the point of it all.
It looks nice in the admin interface as well:

.. image:: https://ucarecdn.com/84e614e4-8faf-4090-ba3a-83294715434b/

Obviously, you would want to use Uploadcare field outside an admin.
It's going to work just as well, but, however, you have to remember to add
``{{ form.media }}`` in the ``<head>`` tag of your page:

.. code-block:: django

    {{ form.media }}

    <form action="" method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <input type="submit" value="Save"/>
    </form>

This is a default Django form property which is going to render any scripts
needed for the form to work, in our case – Uploadcare scripts.

Using it in templates
~~~~~~~~~~~~~~~~~~~~~

You can construct url with all effects manually:

.. code-block:: django

    {% for photo in photos %}
        {{ photo.title }}
        {{ photo.photo.cdn_url }}-/resize/400x300/-/effect/flip/-/effect/grayscale/
    {% endfor %}

Refer to `CDN docs`_ for more information.

How to use it in command line?
------------------------------

.. code-block:: console

    $ ucare -h

Django Widget
=============

Settings
--------

Besides required ``pub_key``, ``secret`` settings there are optional settings,
for example, ``widget_version`` or ``widget_build``:

.. code-block:: python

    UPLOADCARE = {
        'pub_key': 'demopublickey',
        'secret': 'demoprivatekey',
        'widget_version': '3.x',  // ~= 3.0 (latest)
        'widget_build': 'min',  // without jQuery
        'cdn_base': 'https://cdn.mycompany.com',
    }

PyUploadcare takes assets from Uploadcare CDN by default, e.g.:

.. code-block:: html

    <script src="https://ucarecdn.com/widget/x.y.z/uploadcare/uploadcare.full.min.js"></script>

If you don't want to use hosted assets you have to turn off this feature:

.. code-block:: python

    UPLOADCARE = {
        # ...
        'use_hosted_assets': False,
    }

In this case local assets will be used.

If you want to provide custom url for assets then you have to specify
widget url:

.. code-block:: python

    UPLOADCARE = {
        # ...
        'use_hosted_assets': False,
        'widget_url': 'http://path.to/your/widget.js',
    }

`Uploadcare widget`_ will use default upload handler url, unless you specify:

.. code-block:: python

    UPLOADCARE = {
        # ...
        'upload_base_url' = 'http://path.to/your/upload/handler',
    }


Model Fields
------------

As you will see, with Uploadcare, adding and working with a file field is
just as simple as with a `TextField`_. To attach Uploadcare files to a model,
you can use a :ref:`FileField <django-widget-models-filefield-ref>` or
:ref:`ImageField <django-widget-models-imagefield-ref>`.
These fields play by common Django rules. South migrations are supported.

.. note::
    When you call ``your_model_form.is_valid()`` or call ``photo.full_clean()``
    directly it invokes ``File.store()`` method automatically. In other cases
    you should store objects manually, e.g:

    .. code-block:: python

        photo.photo_2x3 = File('a771f854-c2cb-408a-8c36-71af77811f3b')
        photo.save()

        photo.photo_2x3.store()

FileField
~~~~~~~~~

``FileField`` does not require an uploaded file to be any certain format.

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import FileField


    class Candidate(models.Model):

        resume = FileField()

ImageField
~~~~~~~~~~

``ImageField`` requires an uploaded file to be an image. An optional parameter
``manual_crop`` enables, if specified, a manual cropping tool: your user can
select a part of an image she wants to use. If its value is an empty string,
the user can select any part of an image; you can also use values like
``"3:4"`` or ``"200x300"`` to get exact proportions or dimensions of resulting
image. Consult `widget documentation`_ regarding setting up the manual crop:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import ImageField


    class Candidate(models.Model):

        photo = ImageField(blank=True, manual_crop="")

.. image:: https://ucarecdn.com/93b254a3-8c7a-4533-8c01-a946449196cb/-/resize/800/manual_crop.png

Advanced widget options
~~~~~~~~~~~~~~~~~~~~~~~

You can pass any widget options via ``FileWidget``'s attrs argument:

.. code-block:: python

    from django import forms

    from pyuploadcare.dj.forms import FileWidget, ImageField


    # optional. provide advanced widget options: https://uploadcare.com/docs/uploads/widget/config/#options
    class CandidateForm(forms.Form):
        photo = ImageField(widget=FileWidget(attrs={
            'data-cdn-base': 'https://cdn.super-candidates.com',
            'data-image-shrink': '1024x1024',
        }))

FileGroupField
~~~~~~~~~~~~~~

``FileGroupField`` allows you to upload more than one file at a time. It stores
uploaded files as a group:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import FileGroupField


    class Book(models.Model):

        pages = FileGroupField()

ImageGroupField
~~~~~~~~~~~~~~~

``ImageGroupField`` allows you to upload more than one **image** at a time.
It stores uploaded images as a group:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import ImageGroupField


    class Gallery(models.Model):

        photos = ImageGroupField()

Core API
========

Initialization
--------------

You can use pyuploadcare in any Python project. You need to pass
your project keys to ``Uploadcare`` client::

    from pyuploadcare import Uploadcare
    uploadcare = Uploadcare(public_key='<your public key>', secret_key='<your private key>')

Uploading files
---------------

Upload single file. ``File.upload`` method can accept file object or URL. Depending of file object size
direct or multipart upload method will be chosen::

    with open('file.txt') as file_object:
        ucare_file: File = uploadcare.upload(file_object)


Upload file from url::

    ucare_file: File = uploadcare.upload("https://github.githubassets.com/images/modules/logos_page/Octocat.png")

Upload multiple files. Direct upload method is used::

    file1 = open('file1.txt')
    file2 = open('file2.txt')
    ucare_files: List[File] = uploadcare.upload_files([file1, file2])

Send single file via multipart upload::

    with open('file.txt') as file_object:
        ucare_file: File = uploadcare.upload(file_object)

``Uploadcare.upload`` method accepts optional callback function to track uploading progress.
Example of using callback function for printing progress::

    >>> def print_progress(info: UploadProgress):
    ...     print(f'{info.done}/{info.total} B')

    >>> # multipart upload is used
    >>> with open('big_file.jpg', 'rb') as fh:
    ...    uploadcare.upload(fh, callback=print_progress)
    0/11000000 B
    5242880/11000000 B
    10485760/11000000 B
    11000000/11000000 B

    >>> # upload from url is used
    >>> uploadcare.upload("https://github.githubassets.com/images/modules/logos_page/Octocat.png", callback=print_progress)
    32590/32590 B

    >>> # direct upload is used. Callback is called just once after successful upload
    >>> with open('small_file.jpg', 'rb') as fh:
    ...     uploadcare.upload(fh, callback=print_progress)
    56780/56780 B

List files
----------

Get list of files::

    files: FileList = uploadcare.list_files(stored=True, limit=10)
    for file in files:
        print(file.info)

Retrieve files
--------------

Get existing file::

    file: File = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    print(file.info)

Store files
-----------

Store single file::

    file: File = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    file.store()

Store multiple files::

    files = [
        '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
        'a771f854-c2cb-408a-8c36-71af77811f3b'
    ]
    uploadcare.store_files(files)

Delete files
------------

Delete single file::

    file: File = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    file.delete()

Delete multiple files::

    files = [
        '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
        'a771f854-c2cb-408a-8c36-71af77811f3b'
    ]
    uploadcare.delete_files(files)

Video conversion
----------------

Uploadcare can encode video files from all popular formats, adjust their quality, format and dimensions, cut out a video fragment, and generate thumbnails via REST API.

After each video file upload you obtain a file identifier in UUID format. Then you can use this file identifier to convert your video in multiple ways::

    file = uploadcare.file('740e1b8c-1ad8-4324-b7ec-112c79d8eac2')
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

    transformation = VideoTransformation().format(VideoFormat.webm).thumbs(2)
    paths: List[str] = [
        transformation.path("740e1b8c-1ad8-4324-b7ec-112c79d8eac2"),
    ]

    response = uploadcare.video_convert_api.convert(paths)
    video_convert_info = response.result[0]
    converted_file = uploadcare.file(video_convert_info.uuid)

    video_convert_status = uploadcare.video_convert_api.status(video_convert_info.token)

Document Conversion
-------------------

Uploadcare allows converting documents to the following target formats: doc, docx, xls, xlsx, odt, ods, rtf, txt, pdf, jpg, png. Document Conversion works via our REST API.

After each document file upload you obtain a file identifier in UUID format. Then you can use this file identifier to convert your document to a new format::

    file = uploadcare.file('0e1cac48-1296-417f-9e7f-9bf13e330dcf')
    transformation = DocumentTransformation().format(DocumentFormat.pdf)
    converted_file: File = file.convert(transformation)

or create an image of a particular page (if using image format)::

    file = uploadcare.file('5dddafa0-a742-4a51-ac40-ae491201ff97')
    transformation = DocumentTransformation().format(DocumentFormat.png).page(1)
    converted_file: File = file.convert(transformation)

or you can use API directly to convert single or multiple files::

    transformation = DocumentTransformation().format(DocumentFormat.pdf)

    paths: List[str] = [
        transformation.path("0e1cac48-1296-417f-9e7f-9bf13e330dcf"),
    ]

    response = uploadcare.document_convert_api.convert([path])
    document_convert_info = response.result[0]
    converted_file = uploadcare.file(document_convert_info.uuid)

    document_convert_status = uploadcare.document_convert_api.status(document_convert_info.token)


Webhooks
^^^^^^^^

Create a webhook::

    webhook: Webhook = uploadcare.create_webhook("https://path/to/webhook")

Create a webhook with a signing secret::

    webhook = uploadcare.create_webhook(
        target_url="https://path/to/webhook",
        signing_secret="7kMVZivndx0ErgvhRKAr",
    )

List webhooks::

    webhooks: List[Webhook] = list(uploadcare.list_webhooks(limit=10))

Update a webhook::

    webhook: Webhook = uploadcare.update_webhook(webhook_id, is_active=False)

Update a webhook's signing secret::

    webhook: Webhook = uploadcare.update_webhook(webhook_id, signing_secret="7kMVZivndx0ErgvhRKAr")

Delete a webhook::

    uploadcare.delete_webhook(webhook_id)


Projects
^^^^^^^^

Get project info::

    project_info: ProjectInfo = uploadcare.get_project_info()


Image transformations
---------------------

Uploadcare allows to apply image transformations to files. ``File.cdn_url`` attribute returns CDN url::

    >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
    >>> file_.cdn_url
    https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/

You can set default effects by string::

    >>> file_.set_effects('effect/flip/-/effect/mirror/')
    >>> file_.cdn_url
    https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/-/effect/mirror/

or by image transformation builder::

    >>> file_.set_effects(ImageTransformation().grayscale().flip())
    >>> file_.cdn_url
    https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/grayscale/-/flip/

Create file group
-----------------

Create file group::

    file_1: File = uploadcare.file('6c5e9526-b0fe-4739-8975-72e8d5ee6342')
    file_2: File = uploadcare.file('a771f854-c2cb-408a-8c36-71af77811f3b')
    file_group: FileGroup = uploadcare.create_file_group([file_1, file_2])


Retreive file group
-------------------

Get file group::

    file_group: FileGroup = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
    print(file_group.info())

Store file group
----------------

Stores all group's files::

    file_group: FileGroup = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
    file_group.store()

List file groups
----------------

List file groups::

    file_groups: List[FileGroup] = uploadcare.list_file_groups(limit=10)
    for file_group in file_groups:
        print(file_group.info)


Create webhook
--------------

Create webhook::

    webhook: Webhook = uploadcare.create_webhook("https://path/to/webhook")

List webhooks
-------------

List webhooks::

    webhooks: List[Webhook] = list(uploadcare.list_webhooks(limit=10))

Update webhook
--------------

Update webhook::

    webhook: Webhook = uploadcare.update_webhook(webhook_id, is_active=False)

Delete webhook
--------------

Delete webhook::

    uploadcare.delete_webhook(webhook_id)


Get project info
----------------

Get project info::

    project_info: ProjectInfo = uploadcare.get_project_info()


Secure delivery
---------------

You can use your own custom domain and CDN provider for deliver files with authenticated URLs (see original documentation).

Generate secure for file::

    from pyuploadcare import Uploadcare
    from pyuploadcare.secure_url import AkamaiSecureUrlBuilder

    secure_url_bulder = AkamaiSecureUrlBuilder("your cdn>", "<your secret for token generation>")

    uploadcare = Uploadcare(
        public_key='<your public key>',
        secret_key='<your private key>',
        secure_url_builder=secure_url_bulder,
    )

    secure_url = uploadcare.generate_secure_url('52da3bfc-7cd8-4861-8b05-126fef7a6994')

Generate secure for file with transformations::

    secure_url = uploadcare.generate_secure_url(
        '52da3bfc-7cd8-4861-8b05-126fef7a6994/-/resize/640x/other/transformations/'
    )

Deprecated Bits
===============

This part of the documentation contains things that eventually will be deleted.

``UPLOADCARE['widget_variant']`` Django setting. Use ``UPLOADCARE['widget_build']`` instead.

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

.. _hello@uploadcare.com: mailto:hello@uploadcare.com
.. _Uploadcare: https://uploadcare.com/?utm_source=github&utm_campaign=pyuploadcare
.. _simple steps: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
.. _REST: https://uploadcare.com/api-refs/rest-api/?utm_source=github&utm_campaign=pyuploadcare
.. _Upload: https://uploadcare.com/api-refs/upload-api/?utm_source=github&utm_campaign=pyuploadcare
.. _original documentation: https://uploadcare.com/docs/security/secure-delivery/?utm_source=github&utm_campaign=pyuploadcare
.. _here: https://github.com/uploadcare/pyuploadcare-example
.. _bugbounty@uploadcare.com: mailto:bugbounty@uploadcare.com
.. _Github Actions: https://github.com/uploadcare/pyuploadcare/actions
.. _widget documentation: https://uploadcare.com/docs/uploads/widget/crop_options/
.. _TextField: https://docs.djangoproject.com/en/1.8/ref/models/fields/#django.db.models.TextField
.. _CDN docs: https://uploadcare.com/docs/delivery/