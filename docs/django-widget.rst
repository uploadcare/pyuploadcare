.. _django-widget:

=============
Django Widget
=============

.. _django-widget-settings-ref:


Settings
--------

The minimal configuration for a Django project using Uploadcare looks like this:

.. code-block:: python

    UPLOADCARE = {
        "pub_key": "<your public key>",
        "secret": "<your private key>",
    }

You can generate these keys in your project settings on the `Uploadcare dashboard`_.

In addition to the required settings `pub_key` and `secret`, there are several optional settings available.

Below is the full default configuration:

.. code-block:: python

    UPLOADCARE = {
        "pub_key": "",
        "secret": "",
        "cdn_base": None,
        "upload_base_url": None,
        "signed_uploads": False,
        "use_legacy_widget": False,
        "use_hosted_assets": True,
        "widget": {
            "version": "0.36.0",
            "variant": "regular",
            "build": "min",
            "options": {},
            "override_js_url": None,
            "override_css_url": {
                "regular": None,
                "inline": None,
                "minimal": None,
            },
        },
        "legacy_widget": {
            "version": "3.x",
            "build": "full.min",
            "override_js_url": None,
        },
    }

PyUploadcare takes assets from CDN by default, e.g.:

.. code-block:: html

    <script type="module">
        import * as LR from "https://cdn.jsdelivr.net/npm/@uploadcare/blocks@0.x/web/blocks.min.js";
        LR.registerBlocks(LR);
    </script>

    <!-- ... -->

    <lr-file-uploader-inline
        css-src="https://cdn.jsdelivr.net/npm/@uploadcare/blocks@0.x/web/lr-file-uploader-regular.min.css"
        ctx-name="my-uploader"
    ></lr-file-uploader-inline>

If you don't want to use hosted assets you have to turn off this feature:

.. code-block:: python

    UPLOADCARE = {
        # ...
        "use_hosted_assets": False,
    }

In this case local assets will be used.

If you want to provide custom url for assets then you have to specify
widget url:

.. code-block:: python

    UPLOADCARE = {
        # ...
        "widget": {
            "override_js_url": "http://path.to/your/blocks.js",
            "override_css_url": {
                "regular": "http://path.to/your/lr-file-uploader-regular.css", 
                "inline": "http://path.to/your/lr-file-uploader-inline.css", 
                "minimal": "http://path.to/your/lr-file-uploader-minimal.css", 
            },
        },
    }

`Uploadcare widget`_ will use default upload handler url, unless you specify:

.. code-block:: python

    UPLOADCARE = {
        # ...
        "upload_base_url": "http://path.to/your/upload/handler",
    }

Use ``widget_options`` to pass arbitrary `options`_ to the file uploader:

.. code-block:: python

    UPLOADCARE = {
        # ...
        "widget": {
            "options": {
                "source-list": "local,url,camera",
                "camera-mirror": True,
            },
        },
    }


.. _django-legacy-widget-settings-ref:


Settings for legacy widget
--------------------------

If you want to use our legacy jQuery-widget, you can enable it in settings:

.. code-block:: python

    UPLOADCARE = {
        "pub_key": "<your public key>",
        "secret": "<your private key>",
        "use_legacy_widget": True,
    }

Settings that are specific to the legacy widget are prefixed with ``legacy_``:

.. code-block:: python

    UPLOADCARE = {
        # ...
        "use_legacy_widget": True,
        "legacy_widget": {
            "version": "3.x",  # ~= 3.0 (latest)
            "build": "min",  # without jQuery
            "override_js_url": "http://path.to/your/uploadcare.js",
        },
    }

If you have signed uploads enabled in your Uploadcare project, widget-based uploads will fail unless you enable the ``signed_uploads`` setting in your Django project:

.. code-block:: python

    UPLOADCARE = {
        # ...,
        'signed_uploads': True,
    }

.. _django-widget-models-ref:


Model Fields
------------

.. _Uploadcare widget: https://uploadcare.com/docs/uploads/widget/

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

        photo.photo_2x3 = File("a771f854-c2cb-408a-8c36-71af77811f3b")
        photo.save()

        photo.photo_2x3.store()

.. _django-widget-models-filefield-ref:


FileField
~~~~~~~~~

``FileField`` does not require an uploaded file to be any certain format.

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import FileField


    class Candidate(models.Model):

        resume = FileField()

.. _django-widget-models-imagefield-ref:


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

.. _django-widget-models-imagefield-advanced-ref:


Advanced widget options
~~~~~~~~~~~~~~~~~~~~~~~

You can pass any widget `options`_ via ``FileWidget``'s attrs argument:

.. code-block:: python

    from django import forms

    from pyuploadcare.dj.forms import FileWidget, ImageField

    # Optional: provide advanced widget options https://uploadcare.com/docs/file-uploader/options/
    class CandidateForm(forms.Form):
        photo = ImageField(widget=FileWidget(attrs={
            "source-list": "local,url,camera",
            "camera-mirror": True,
        }))

Use ``LegacyFileWidget`` whenever you want to switch back to jQuery-based
widget on a field-by-field basis without turning it on globally (using
``"use_legacy_widget": True``).

.. code-block:: python

    from django import forms

    from pyuploadcare.dj.forms import LegacyFileWidget, ImageField

    class CandidateForm(forms.Form):
        photo = ImageField(widget=LegacyFileWidget)


.. _django-widget-models-filegroupfield-ref:


FileGroupField
~~~~~~~~~~~~~~

``FileGroupField`` allows you to upload more than one file at a time. It stores
uploaded files as a group:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import FileGroupField


    class Book(models.Model):

        pages = FileGroupField()

.. _django-widget-models-imagegroupfield-ref:


ImageGroupField
~~~~~~~~~~~~~~~

``ImageGroupField`` allows you to upload more than one **image** at a time.
It stores uploaded images as a group:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj.models import ImageGroupField


    class Gallery(models.Model):

        photos = ImageGroupField()


.. _Uploadcare dashboard: https://app.uploadcare.com/
.. _options: https://uploadcare.com/docs/file-uploader/options/
.. _widget documentation: https://uploadcare.com/docs/file-uploader/options/#crop-preset
.. _TextField: https://docs.djangoproject.com/en/4.2/ref/models/fields/#textfield
