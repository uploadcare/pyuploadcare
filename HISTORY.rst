.. :changelog:

History
-------

1.0.1
~~~~~

- Widget was updated up to *0.8.1.2*.
- It was invocating ``File.store()``, ``FileGroup.store()`` methods on every
  model instance saving into database, e.g.:

  .. code-block:: python

      photo.title = 'new title'
      photo.save()

  Now it happens while saving by form only, namely by calling
  ``form.is_valid()``. There are other things that can trigger storing
  (accessing the ``form.errors`` attribute or calling ``form.full_clean()``
  directly).

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
- More apropriate exceptions were added.
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
