.. _django-widget:

=============
Django Widget
=============

.. _django-widget-settings-ref:

Settings
--------

Besides required ``pub_key``, ``secret`` settings there are optional settings,
for example, ``widget_version`` or ``widget_build``:

.. code-block:: python

    UPLOADCARE = {
        'pub_key': 'demopublickey',
        'secret': 'demoprivatekey',
        'widget_version': '2.5.0',
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

.. _django-widget-models-ref:

Model Fields
------------

.. _Uploadcare widget: https://uploadcare.com/documentation/widget/

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

.. _django-widget-models-filefield-ref:

FileField
~~~~~~~~~

``FileField`` does not require an uploaded file to be any certain format.

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj import FileField


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

    from pyuploadcare.dj import ImageField


    class Candidate(models.Model):

        photo = ImageField(blank=True, manual_crop="")

.. image:: https://ucarecdn.com/93b254a3-8c7a-4533-8c01-a946449196cb/-/resize/800/manual_crop.png

.. _django-widget-models-filegroupfield-ref:


Advanced widget options
~~~~~~~~~~~~~~~~~~~~~~~

You can pass any widget options via ``FileWidget``'s attrs argument:

.. code-block:: python

    from django import forms

    from pyuploadcare.dj.forms import FileWidget, ImageField


    # optional. provide advanced widget options: https://uploadcare.com/documentation/widget/#configuration
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

    from pyuploadcare.dj import FileGroupField


    class Book(models.Model):

        pages = FileGroupField()

.. _django-widget-models-imagegroupfield-ref:

ImageGroupField
~~~~~~~~~~~~~~~

``ImageGroupField`` allows you to upload more than one **image** at a time.
It stores uploaded images as a group:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj import ImageGroupField


    class Gallery(models.Model):

        photos = ImageGroupField()

.. _widget documentation: https://uploadcare.com/documentation/widget/#crop
.. _TextField: https://docs.djangoproject.com/en/1.8/ref/models/fields/#django.db.models.TextField
