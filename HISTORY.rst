.. :changelog:

History
-------

1.2.15
~~~~~~

- update widget to 2.3.1 (see `widget changelog`_)


1.2.14
~~~~~~

- update widget to 1.5.5 (see `widget changelog`_)


1.2.13
~~~~~~

- improve synchronous upload API
- fix encoding issues with pip3
- update widget to 1.5.4 (see `widget changelog`_)
- add AUTHORS.txt


1.2.12
~~~~~~

- add synchronous upload from URL method to `File`
- UploadcareExceptions are `__repr__`'ed properly
- update widget to 1.5.3 (see `widget changelog`_)


1.2.11
~~~~~~

- fix "source" composition for copy requests
- let configure default throttle retry count via `conf.retry_throttled`


1.2.10
~~~~~~

- handle responses for HEAD and OPTION requests
- update widget to 1.4.6


1.2.9
~~~~~

- compatibility with Django 1.7


1.2.8
~~~~~

- update widget to 1.4.0


1.2.7
~~~~~

- handle rest api throttling


1.2.6
~~~~~

- update widget to 1.2.3
- fixed compatibility with six library version 1.7.0 and above


1.2.5
~~~~~

- fixed setup script


1.2.4
~~~~~

- update widget to 1.0.1
- fixed logging when response contains unicode chars


1.2.3
~~~~~

- update widget to 0.17.1


1.2.2
~~~~~

- add File.copy()
- add data attribute to UploadcareException
- update widget to 0.13.2
- update pyuploadcare.dj.models.ImageField crop validation


1.2.1
~~~~~

``https://ucarecdn.com/`` URL was returned to serve widget's assets.


1.2
~~~

- CDN URL has been changed to ``http://www.ucarecdn.com/``. Previous URL
  ``https://ucarecdn.com/`` is depricated.
- Widget was updated up to *0.10.1*.

1.1
~~~

- Widget was updated up to *0.10*.
- Default API version was updated up to *0.3*.
- Django settings were merged into UPLOADCARE dictionary.
- Performance was improved by reusing requests' session.

1.0.2
~~~~~

``UnicodeDecodeError`` was fixed. This bug appears when
`request <https://pypi.python.org/pypi/requests/>`_'s ``method``
param is unicode and ``requests.request()`` got ``files`` argument, e.g.:

.. code-block:: python

    >>> requests.request(u'post', u'http://httpbin.org/post',
    ...                  files={u'file': open('README.rst', 'rb')})
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc5 ...

1.0.1
~~~~~

- Widget was updated up to *0.8.1.2*.
- It was invoking ``File.store()``, ``FileGroup.store()`` methods on every
  model instance saving, e.g.:

  .. code-block:: python

      photo.title = 'new title'
      photo.save()

  Now it happens while saving by form, namely by calling
  ``your_model_form.is_valid()``. There is other thing that can trigger
  storing -- calling ``photo.full_clean()`` directly.

1.0
~~~

- Python 3.2, 3.3 support were added.
- File Group creating was added.
- Methods per API field for File, FileGroup were added.
- Deprecated things were deleted. This version is not backward compatible.
  For detailed information see
  https://pyuploadcare.readthedocs.org/en/v0.19/deprecated.html

0.19
~~~~

- Multiupload support was added.
- ``argparse`` was added into ``setup.py`` requirements.
- Documentation was added and published on https://pyuploadcare.readthedocs.org

0.18
~~~~

- Widget was updated up to *0.6.9.1*.

0.17
~~~~

- ``ImageField`` was added. It provides uploading only image files. Moreover,
  you can activate manual crop, e.g. ``ImageField(manual_crop='2:3')``.
- More appropriate exceptions were added.
- Tests were separated from library and were restructured.
- Widget was updated up to *0.6.7*.
- Issue of ``FileField``'s ``blank``, ``null`` attributes was fixed.

0.14
~~~~

- Replace accept header for old api version

0.13
~~~~

- Fix unicode issue on field render

0.12
~~~~

- Add new widget to pyuploadcare.dj
- Remove old widget
- Use https for all requests

0.11
~~~~

- Add cdn_base to Ucare.__init__
- Get rid of api v.0.1 support
- Add File.ensure_on_s3 and File.ensure_on_cdn helpers
- Add File properties is_on_s3, is_removed, is_stored
- Fix url construction
- Add and correct waiting to upload and upload_from_url

0.10
~~~~

- Add console log handler to ucare
- Add wait argument to ucare store and delete commands
- Fix ucare arg handling

0.9
~~~

- Add bunch of arguments to ucare upload and upload_via_url commands
- Fix UploadedFile.wait()

0.8
~~~

- Fix file storing for old API
- Replaced Authentication header with Authorization
- Log warnings found in HTTP headers
- Replace old resizer with new CDN
- Add verify_api_ssl, verify_upload_ssl options
- Add custom HTTP headers to API and upload API requests

0.7
~~~

- Added __version__
- Added 'User-Agent' request header
- Added 'Accept' request header
- Added ucare config file parsing
- Added pyuploadcare/tests.py
- Replaced upload API
- Replaced File.keep with File.store, File.keep is deprecated
- File.store uses new PUT request
- Added timeouts to File.store, File.delete
- Added upload and upload_from_url to ucare
- Added tests during setup
- Replaced httplib with requests, support https (certificates for api requests are verified)
- Added api_version arg to UploadCare, default is 0.2

0.6
~~~

- Added ucare cli utility
- Added PYUPLOADCARE_UPLOAD_BASE_URL setting
- Added PYUPLOADCARE_WIDGET_URL
- Updated widget assets to version 0.0.1
- Made properties out of following pyuploadcare.file.File's methods:

  - api_uri()
  - url()
  - filename()
- Changed pyuploadcare.UploadCareException.__init__


.. _widget changelog: https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown
