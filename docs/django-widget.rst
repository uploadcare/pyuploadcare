.. _django-widget:

=============
Django Widget
=============

.. _django-widget-settings-ref:

Settings
--------

PyUploadcare takes assets from Uploadcare CDN by default, e.g.:

.. code-block:: html

    <script src="https://ucarecdn.com/widget/x.y.z/uploadcare/uploadcare-x.y.z.min.js"></script>

If you don't want to use hosted assets you have to turn off this feature:

.. code-block:: python

    PYUPLOADCARE_USE_HOSTED_ASSETS = False

In this case local assets will be used.

If you want to provide custom url for assets then you have to specify
widget url:

.. code-block:: python

    PYUPLOADCARE_USE_HOSTED_ASSETS = False
    PYUPLOADCARE_WIDGET_URL = 'http://path.to/your/widget.js'

`Uploadcare widget`_ will use default upload handler url, unless you specify:

.. code-block:: python

    PYUPLOADCARE_UPLOAD_BASE_URL = 'http://path.to/your/upload/handler'

.. _django-widget-models-ref:

Model Fields
------------

.. _Uploadcare widget: https://uploadcare.com/documentation/widget/
