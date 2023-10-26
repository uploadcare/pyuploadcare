# History

All notable changes to this project will be documented in this file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.4](https://github.com/uploadcare/pyuploadcare/compare/v4.1.3...v4.1.4) - 2023-10-27

This update introduces the ability to generate secure URLs with the same signature valid not only for the base URL of the file (e.g., `https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/`) but also for all of its transformations (#264). This is optional by default.

Also, `AkamaiSecureUrlBuilderWithUrlToken` class has been implemented (#263).

### Added

- For `Uploadcare`
  - added optional `wildcard` parameter to `generate_secure_url` method.

- For `AkamaiSecureUrlBuilderWithAclToken`:
  - added optional `wildcard` parameter to `build` method.

- `AkamaiSecureUrlBuilderWithUrlToken` class.

### Changed

- `AkamaiSecureUrlBuilder` has been renamed to `AkamaiSecureUrlBuilderWithAclToken`. It is still available under the old name and works as before, but it will give you a deprecation warning when you use it.

## [4.1.3](https://github.com/uploadcare/pyuploadcare/compare/v4.1.2...v4.1.3) - 2023-10-05

### Added

- For `AudioStreamInfo`:
  - added `profile` field.

### Changed

- `pyuploadcare` now officially supports Python 3.12 (please notice that if you're using Django, that doesn't support Python 3.12 as of yet).

## [4.1.2](https://github.com/uploadcare/pyuploadcare/compare/v4.1.1...v4.1.2) - 2023-09-08

### Fixed

- Incorrect expiration time was calculated for signed uploads causing the `AuthenticationError: Expired signature` exception.

## [4.1.1](https://github.com/uploadcare/pyuploadcare/compare/v4.1.0...v4.1.1) - 2023-09-04

### Fixed

- Resolved a `ValidationError` that occurred when requesting file information for specific video files.

## [4.1.0](https://github.com/uploadcare/pyuploadcare/compare/v4.0.0...v4.1.0) - 2023-07-18

### Added

- For `Uploadcare` and `UploadAPI`:
  - `upload_from_url` and `upload_from_url_sync` can now accept two new optional parameters: `check_duplicates` and `save_duplicates`. These correspond to `check_URL_duplicates` and `save_URL_duplicates` for [`/from_url/` upload API endpoint](https://uploadcare.com/api-refs/upload-api/#tag/Upload/operation/fromURLUpload) respectively.
- For `FileGroup`:
  - The `delete` method now includes an optional `delete_files` argument, which indicates whether the files within the specified group should also be deleted.

### Changed

- Bumped `httpx` dependency for py37+.
- Bumped `yarl` dev dependency for py37+.
- Bumped `coverage` dev dependency for py37+.
- Tests are now run against Python 3.11 as well. The minimum supported version of Python remains 3.6.
- Tests are now run against Django 4.0, 4.1 and 4.2 as well. The minimum supported version of Django remains 1.11.

## [4.0.0](https://github.com/uploadcare/pyuploadcare/compare/v3.2.0...v4.0.0) - 2022-12-26

Now uses [REST API v0.7](https://uploadcare.com/api-refs/rest-api/v0.7.0/#tag/Changelog).

### Breaking changes

- For `File.info`:
  - File information doesn't return `image_info` and `video_info` fields anymore,
  they were moved into field `content_info` that includes mime-type, image (dimensions, format, etc), video information (duration, format, bitrate, etc), audio information, etc.
  - Removed `rekognition_info` in favor of `appdata`.
- For `file_list` method of `FileList`:
  - Removed the option of sorting the file list by file size.
- For `File`:
  - Removed method `copy` in favor of `local_copy` and `remote_copy` methods.
  - Files to upload must be opened in a binary mode.

### Added

- For `File.info`:
  - Field `metadata` that includes arbitrary metadata associated with a file.
  - Field `appdata` that includes dictionary of application names and data associated with these applications.
- Add Uploadcare API interfaces for `Uploadcare`:
    - `MetadataAPI`
    - `AddonsAPI`
- Added an option to delete a Group.

### Fixed

  - Limit for batch operation is set to 100 [(doc)](https://uploadcare.com/api-refs/rest-api/v0.7.0/#operation/filesStoring).
  - Iterating over long collections in batch operation.
  - Akamai signed URL generation.

## [3.2.0](https://github.com/uploadcare/pyuploadcare/compare/v3.1.0...v3.2.0) - 2022-12-19

### Changed

  - Freezed `httpx` dependency for py37+ (`=0.23.0`) to prevent breaking changes in processing files opened in the text mode.

### Fixed

  - Akamai signed URL generation.
  
## [3.1.0](https://github.com/uploadcare/pyuploadcare/compare/v3.0.1...v3.1.0) - 2022-10-24

### Changed

  - Bumped `httpx` dependency for py37+.
  - Add `follow_redirects` argument for Client request method.
  - Using `allow_redirects` argument is allowed, but will cause a deprecating warning.
  - Bumped `black` dependency.

## [3.0.1](https://github.com/uploadcare/pyuploadcare/compare/v3.0.0...v3.0.1) - 2022-10-06

### Changed

  - Bumped `pytz` dependency.
  - Bumped `typing-extensions` for py37+.

## [3.0.0](https://github.com/uploadcare/pyuploadcare/compare/v2.7.0...v3.0.0) - 2021-11-01

### Added

  - Multipart uploads.
  - Document and video conversions.
  - Authenticated URL generator.
  - Image transformation path builder.
  - Webhook operations.
  - Getting project information.
  - Low-level API.
  - `Uploadcare` client.

### Changed

  - Dropped support for Python 3.5.
  - Dropped support for Python 2.\*.
  - Allowed uploading from URL in `File.upload` method.
  - Resource attributes can be accessed now as properties, not methods.
  - `Uploadcare` client should be initialized to access API.
  - Moved from Travis to Github Actions.

## [2.7.0](https://github.com/uploadcare/pyuploadcare/compare/v2.6.0...v2.7.0) - 2020-05-03

### Added

  - Support for signed uploads.

### Changed

  - Dropped support for Python 3.4.
  - Update bundled widget to version `3.6.1`. See [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown).

### Fixed

  - Tests.

## [2.6.0](https://github.com/uploadcare/pyuploadcare/compare/v2.5.0...v2.6.0) - 2018-11-29

### Changed

  - Improved error logging.
  - Update bundled widget to version `3.6.1`. See [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown).

### Fixed

  - `FileWidget.render()` now works in
    Django 2.1.
  - Obsolete widget setting
    `data-upload-base-url` replaced with
    `data-url-base`

## 2.5.0

  - Update bundled widget to version `3.3.0`. See [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown).
  - Update links to the Uploadcare site
  - Expand data format in 'User-Agent' request header.

## 2.4.0

  - Change data format in 'User-Agent' request header.

## 2.3.1

  - Update default widget version to `3.x`
  - Update bundled widget to version `3.2.3`. See [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown).

## 2.3.0

  - Add support for Django versions 1.11 and \~2.0
  - Miscellaneous updates (version, year in a license file, tox
    configuration and etc.)
  - Drop official support for obsolete Python and Django versions.
    Chances are that everything still works. If you have to use those,
    modify `tox.ini`, run tests and use at
    your own risk ;) Or, you may use older versions of the library.

## 2.2.1

  - Add `file.create_local_copy` and `file.create_remote_copy` methods.
  - Add new `make_public` and `pattern` parameters to
    file.create\_remote\_copy method.
  - Add new `store` parameter to file.create\_local\_copy methods.
  - Update CDN link to the widget.
  - Use wildcard `2.x` to always get the latest patch or minor version
    of widget version `2`. See [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown).
  - Update bundled widget to version `2.10.3`. See [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown).

## 2.1.0

  - Support auto storing in upload requests
  - Updated widget to version 2.10.0 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown)).
  - Drop support for Python 3.2
  - Simplify and reduce test matrix in `.travis.yml`

## 2.0.1

  - Fixed issue with missing `ucare_cli` package.

## 2.0

  - Added support for version 0.5 of REST API.
  - Updated widget to version 2.8.1 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown)).
  - Added the `ucare list_groups` command.
  - Removed deprecated entities.

**NB**: There are backward incompatible changes. For detailed
information about the upgrade process see [update to version 2.0](https://pyuploadcare.readthedocs.io/en/stable/install.html#update-to-version-2-0).

## 1.3.6

  - Fixed ZeroDivision error when trying to sync files with no size

## 1.3.5

  - Added support of Django 1.9
  - Removed indication of Unicode strings from output of `ucare`
  - Fixed a group representation for `ucare create_group` command
  - Fixed error with `ucare sync` when trying to processing of not image files

## 1.3.4

  - Added storage operations
  - Added request\_limit to ucare\_cli

## 1.3.3

  - Expanded User-Agent

## 1.3.2

  - Added sync command to ucare\_cli
  - Autogenerated documentation for ucare\_cli
  - update widget to 2.5.5 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))

## 1.3.1

  - Default CDN base to <https://ucarecdn.com>
  - Allow changing CDN base via Django settings
  - update widget to 2.5.0 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))

## 1.3.0

  - API version was updated up to *0.4*.
  - update widget to 2.4.0 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))

## 1.2.15

  - update widget to 2.3.1 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))

## 1.2.14

  - update widget to 1.5.5 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))

## 1.2.13

  - improve synchronous upload API
  - fix encoding issues with pip3
  - update widget to 1.5.4 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))
  - add AUTHORS.txt

## 1.2.12

  - add synchronous upload from URL method to `File`
  - UploadcareExceptions are `__repr__`'ed properly
  - update widget to 1.5.3 (see [widget changelog](https://github.com/uploadcare/uploadcare-widget/blob/master/HISTORY.markdown))

## 1.2.11

  - fix "source" composition for copy requests
  - let configure default throttle retry count via `conf.retry_throttled`

## 1.2.10

  - handle responses for HEAD and OPTION requests
  - update widget to 1.4.6

## 1.2.9

  - compatibility with Django 1.7

## 1.2.8

  - update widget to 1.4.0

## 1.2.7

  - handle rest api throttling

## 1.2.6

  - update widget to 1.2.3
  - fixed compatibility with six library version 1.7.0 and above

## 1.2.5

  - fixed setup script

## 1.2.4

  - update widget to 1.0.1
  - fixed logging when response contains unicode chars

## 1.2.3

  - update widget to 0.17.1

## 1.2.2

  - add File.copy()
  - add data attribute to UploadcareException
  - update widget to 0.13.2
  - update pyuploadcare.dj.models.ImageField crop validation

## 1.2.1

`https://ucarecdn.com/` URL was returned to serve widget's assets.

## 1.2

  - CDN URL has been changed to `http://www.ucarecdn.com/`. Previous URL `https://ucarecdn.com/` is depricated.
  - Widget was updated up to *0.10.1*.

## 1.1

  - Widget was updated up to *0.10*.
  - Default API version was updated up to *0.3*.
  - Django settings were merged into UPLOADCARE dictionary.
  - Performance was improved by reusing requests' session.

## 1.0.2

`UnicodeDecodeError` was fixed. This bug appears when
[request](https://pypi.python.org/pypi/requests/)'s `method` param is
unicode and `requests.request()` got `files` argument, e.g.:

``` python
>>> requests.request(u'post', u'http://httpbin.org/post',
...                  files={u'file': open('README.rst', 'rb')})
UnicodeDecodeError: 'ascii' codec can't decode byte 0xc5 ...
```

## 1.0.1

  - Widget was updated up to *0.8.1.2*.

  - It was invoking `File.store()`, `FileGroup.store()` methods on every model instance saving, e.g.:

    ``` python
    photo.title = 'new title'
    photo.save()
    ```

    Now it happens while saving by form, namely by calling
    `your_model_form.is_valid()`. There is other thing that can trigger
    storing -- calling `photo.full_clean()` directly.

## 1.0

  - Python 3.2, 3.3 support were added.
  - File Group creating was added.
  - Methods per API field for File, FileGroup were added.
  - Deprecated things were deleted. This version is not backward
    compatible. For detailed information see
    <https://pyuploadcare.readthedocs.org/en/v0.19/deprecated.html>

## 0.19

  - Multiupload support was added.
  - `argparse` was added into `setup.py` requirements.
  - Documentation was added and published on
    <https://pyuploadcare.readthedocs.org>

## 0.18

  - Widget was updated up to *0.6.9.1*.

## 0.17

  - `ImageField` was added. It provides uploading only image files.
    Moreover, you can activate manual crop, e.g.
    `ImageField(manual_crop='2:3')`.
  - More appropriate exceptions were added.
  - Tests were separated from library and were restructured.
  - Widget was updated up to *0.6.7*.
  - Issue of `FileField`'s `blank`, `null` attributes was fixed.

## 0.14

  - Replace accept header for old api version

## 0.13

  - Fix unicode issue on field render

## 0.12

  - Add new widget to pyuploadcare.dj
  - Remove old widget
  - Use https for all requests

## 0.11

  - Add cdn\_base to Ucare.\_\_init\_\_
  - Get rid of api v.0.1 support
  - Add File.ensure\_on\_s3 and File.ensure\_on\_cdn helpers
  - Add File properties is\_on\_s3, is\_removed, is\_stored
  - Fix url construction
  - Add and correct waiting to upload and upload\_from\_url

## 0.10

  - Add console log handler to ucare
  - Add wait argument to ucare store and delete commands
  - Fix ucare arg handling

## 0.9

  - Add bunch of arguments to ucare upload and upload\_via\_url commands
  - Fix UploadedFile.wait()

## 0.8

  - Fix file storing for old API
  - Replaced Authentication header with Authorization
  - Log warnings found in HTTP headers
  - Replace old resizer with new CDN
  - Add verify\_api\_ssl, verify\_upload\_ssl options
  - Add custom HTTP headers to API and upload API requests

## 0.7

  - Added \_\_version\_\_
  - Added 'User-Agent' request header
  - Added 'Accept' request header
  - Added ucare config file parsing
  - Added pyuploadcare/tests.py
  - Replaced upload API
  - Replaced File.keep with File.store, File.keep is deprecated
  - File.store uses new PUT request
  - Added timeouts to File.store, File.delete
  - Added upload and upload\_from\_url to ucare
  - Added tests during setup
  - Replaced httplib with requests, support https (certificates for api
    requests are verified)
  - Added api\_version arg to UploadCare, default is 0.2

## 0.6

  - Added ucare cli utility
  - Added PYUPLOADCARE\_UPLOAD\_BASE\_URL setting
  - Added PYUPLOADCARE\_WIDGET\_URL
  - Updated widget assets to version 0.0.1
  - Made properties out of following pyuploadcare.file.File's methods:
      - api\_uri()
      - url()
      - filename()
  - Changed pyuploadcare.UploadCareException.\_\_init\_\_
