.. _deprecated:

===============
Deprecated Bits
===============

This part of the documentation contains things that eventually will be deleted.

.. attribute:: pyuploadcare.file.File.file_id
   :noindex:

   Use ``uuid`` instead.

.. attribute:: pyuploadcare.file.File.info
   :noindex:

   Use ``info()`` instead.

.. attribute:: pyuploadcare.file.File.is_stored
   :noindex:

   Use ``is_stored()`` instead.

.. attribute:: pyuploadcare.file.File.is_removed
   :noindex:

   Use ``is_removed()`` instead.

.. attribute:: pyuploadcare.file.File.url
   :noindex:

   Use ``cdn_url`` instead.

.. attribute:: pyuploadcare.file.File.filename
   :noindex:

   Use ``filename()`` instead.

.. attribute:: pyuploadcare.file.File.ucare
   :noindex:

.. attribute:: pyuploadcare.file.File.api_uri
   :noindex:

.. attribute:: pyuploadcare.file.File.storage_uri
   :noindex:

.. attribute:: pyuploadcare.file.File.is_on_s3
   :noindex:

.. method:: pyuploadcare.file.File.ensure_on_s3(timeout=5)
   :noindex:

.. method:: pyuploadcare.file.File.keep(**kwargs)
   :noindex:

   Use ``store(wait=False, timeout=5)`` instead.

.. method:: pyuploadcare.file.File.cropped(width=None, height=None)
   :noindex:

   Contruct url with `crop`_ modificator manually instead.

.. method:: pyuploadcare.file.File.resized(width=None, height=None)
   :noindex:

   Contruct url with `resize`_ modificator manually instead.

.. method:: pyuploadcare.file.File.serialize()
   :noindex:

   Use ``uuid`` instead.

.. exception:: pyuploadcare.exceptions.UploadCareException
   :noindex:

   Use ``UploadcareException`` instead.

.. class:: pyuploadcare.UploadCare
   :noindex:

   Use API resources instead, e.g. ``File``, ``FileGroup``.

*ucare* CLI:

- ``custom_headers`` was removed;
- ``api_url`` was renamed to ``api_base``;
- ``upload_url`` was renamed to ``upload_base``.

.. _crop: `CDN API`_
.. _resize: `CDN API`_
.. _CDN API: https://uploadcare.com/documentation/cdn/
