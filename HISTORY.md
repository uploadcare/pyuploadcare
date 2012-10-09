### 0.9
    * Add --dont_ask argument to ucare upload and upload_via_url commands
    * Fix UploadedFile.wait()


### 0.8
    * Fix file storing for old API
    * Replaced Authentication header with Authorization
    * Log warnings found in HTTP headers
    * Replace old resizer with new CDN
    * Add verify_api_ssl, verify_upload_ssl options
    * Add custom HTTP headers to API and upload API requests


### 0.7
    * Added __version__
    * Added 'User-Agent' request header
    * Added 'Accept' request header
    * Added ucare config file parsing
    * Added pyuploadcare/tests.py
    * Replaced upload API
    * Replaced File.keep with File.store, File.keep is deprecated
    * File.store uses new PUT request
    * Added timeouts to File.store, File.delete
    * Added upload and upload_from_url to ucare
    * Added tests during setup
    * Replaced httplib with requests, support https (certificates for api requests are verified)
    * Added api_version arg to UploadCare, default is 0.2


### 0.6
    * Added ucare cli utility
    * Added PYUPLOADCARE_UPLOAD_BASE_URL setting
    * Added PYUPLOADCARE_WIDGET_URL
    * Updated widget assets to version 0.0.1
    * Made properties out of following pyuploadcare.file.File's methods:
        - api_uri()
        - url()
        - filename()
    * Changed pyuploadcare.UploadCareException.__init__
