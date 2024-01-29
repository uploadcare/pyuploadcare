# Python API client for Uploadcare

[![](https://badge.fury.io/py/pyuploadcare.svg)](https://pypi.org/project/pyuploadcare/)
[![](https://github.com/uploadcare/pyuploadcare/actions/workflows/test.yml/badge.svg)](https://github.com/uploadcare/pyuploadcare/actions?query=branch%3Amain+workflow%3ATests++)
[![](https://readthedocs.org/projects/pyuploadcare/badge/?version=latest)](https://pyuploadcare.readthedocs.io/)
[![](https://img.shields.io/badge/tech-stack-0690fa.svg?style=flat)](https://stackshare.io/uploadcare)

Build file handling in minutes. Upload or accept UGC, store, transform, optimize, and deliver images, videos, and documents to billions of users.

* [Features](#features)
* [Requirements and installation](#requirements-and-installation)
* [Usage example](#usage-example)
* [Documentation](#documentation)
* [Use cases](#use-cases)
* [Demo app](#demo-app)
* [Useful links](#useful-links)

## Features

This library consists of the APIs interface and a couple of Django goodies, 100% covering [Upload](https://uploadcare.com/api-refs/upload-api/), [REST](https://uploadcare.com/api-refs/rest-api/) and [URL](https://uploadcare.com/api-refs/url-api/) Uploadcare APIs.

Enable obsessively friendly file uploads:
* Built-in [File Uploader](https://uploadcare.com/docs/uploads/storage/#file-storing-behavior)
* Upload files from anywhere
* Multipart uploading for large files
* File size and MIME type filtering
* Malware protection
* Signed uploads
* Uploading network to speed up uploading jobs

Store files the way you need:
* Define file storing behaviour
* Create projects with separate settings programmatically
* Connect custom storage

Handle all files smart & RESTfully:
* CRUD files and their metadata
* Scan for unsafe and malicious content
* Convert documents and other files
* Encode and transform videos
* Recognize objects in the image
* Add arbitrary file metadata
* Control events with webhooks

Process images on the fly right before delivery time:
* Compression
* Geometry
* Colors
* Definition
* Overlays
* Rotations
* Recognition

Fast and reliable delivery:
* Worldwide CDN
* Custom CDN CNAME
* Signed URLs
* Search engine indexing behaviour
* Proxy to fetch and deliver remote files

## Requirements and installation

* Python 3.8, 3.9, 3.10, 3.11, 3.12

To use pyuploadcare with Python 3.6 or 3.7 please install `pyuploadcare < 5.0`.

To use pyuploadcare with Python 2.7 please install `pyuploadcare < 3.0`.

Django compatibility:

| Py/Dj | 2.2 | 3.0 | 3.1 | 3.2 | 4.0 |	4.1 | 4.2 | 5.0 |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|
| 3.8   |  X  |  X  |  X  |  X  |  X  |  X  |  X  |     |
| 3.9   |  X  |  X  |  X  |  X  |  X  |  X  |  X  |     |
| 3.10  |     |     |     |  X  |  X  |  X  |  X  |  X  |
| 3.11  |     |     |     |     |     |  X  |  X  |  X  |
| 3.12  |     |     |     |     |     |     |  X  |  X  |

In order to install `pyuploadcare`, run these commands in CLI:

```bash
pip install pyuploadcare
```

or, if you prefer it the old way:

```bash
easy_install pyuploadcare
```

To use in Django project install with extra dependencies:

```bash
pip install pyuploadcare[django]
```

## Usage example

Let's add [File Uploader](https://uploadcare.com/docs/uploads/storage/#file-storing-behavior) to an existing Django project. To do so, follow a few simple steps described in our [quickstart](https://pyuploadcare.readthedocs.org/en/latest/quickstart.html).

This will enable users to see the upload progress, pick files from sources like Google Drive or Instagram, and edit a form while files are being uploaded asynchronously.

```python
    from django import forms
    from django.db import models

    from pyuploadcare.dj.models import ImageField
    from pyuploadcare.dj.forms import FileWidget, ImageField as ImageFormField


    class Candidate(models.Model):
        photo = ImageField(blank=True, manual_crop="")


    # optional. provide advanced widget options: https://uploadcare.com/docs/uploads/widget/config/#options
    class CandidateForm(forms.Form):
        photo = ImageFormField(widget=FileWidget(attrs={
            'data-cdn-base': 'https://cdn.super-candidates.com',
            'data-image-shrink': '1024x1024',
        }))
```

![](https://ucarecdn.com/f0894ef2-352e-406a-8279-737dd6e1f10c/-/resize/800/josi.png)

## Documentation

Detailed specification of this library is available [on RTD](https://pyuploadcare.readthedocs.io/en/latest/).

We highly recommend to check out [Uploadcare documentation](https://uploadcare.com/docs/) to fully understand what our platform enables you.

## Use cases

To help you figure what this library can help you with, we want to showcase some use cases that you can solve with Uploadcare.

Main use cases:
* Accept user-generated content ([file uploader](https://uploadcare.com/docs/file-uploader/), [upload sources](https://uploadcare.com/docs/upload-sources/))
* Serve responsive images ([optimization](https://uploadcare.com/docs/transformations/image/compression/), [proxy](https://uploadcare.com/docs/delivery/proxy/), [adaptive image](https://uploadcare.com/docs/adaptive-image/) and other [integrations](https://uploadcare.com/docs/integrations/))

Common:
* Art-direction of the content on your page ([transformations](https://uploadcare.com/docs/transformations/image/), [remove.bg](https://uploadcare.com/docs/remove-bg/), [smart crop](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-smart-crop), [scale crop](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-scale-crop), [smart resize](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-smart-resize), [zoom](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-zoom-objects), [circle](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-border-radius), [fill](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-setfill))
* Unify accepted video files to web-friendly formats and quality ([encoding](https://uploadcare.com/docs/transformations/video-encoding/))
* Create thumbnails ([videos](https://uploadcare.com/docs/transformations/video-encoding/#operation-thumbs), [documents](https://uploadcare.com/docs/transformations/document-conversion/#thumbnails))
* Validate incoming files ([validation](https://uploadcare.com/docs/moderation/), [NSFW](https://uploadcare.com/docs/unsafe-content/), [malware](https://uploadcare.com/docs/security/malware-protection/))
* Watermark and protect your content ([overlays](https://uploadcare.com/docs/transformations/image/overlay/), [blur](https://uploadcare.com/docs/effects-enhancements/#operation-blur-region) + [baking](https://uploadcare.com/docs/mutability/))
* Optimize the size of animated images ([gif2video](https://uploadcare.com/docs/transformations/gif-to-video/))
* Access control (signed [uploads](https://uploadcare.com/docs/security/secure-uploads/) and [downloads](https://uploadcare.com/docs/security/secure-delivery/))

Less common:
* Image art-direction based on faces or objects ([faces](https://uploadcare.com/docs/intelligence/face-detection/), [objects](https://uploadcare.com/docs/transformations/image/resize-crop/#operation-crop-tags))
* Image delivery when color science is important ([colors](https://uploadcare.com/docs/effects-enhancements/#image-color-profile-management))
* Native uploads on mobile ([iOS](https://uploadcare.com/docs/integrations/swift/), [Android](https://uploadcare.com/docs/integrations/android/))
* SVG transformations ([rasterization](https://uploadcare.com/docs/transformations/image/svg/))
* Remove geolocation data ([strip](https://uploadcare.com/docs/transformations/image/compression/#meta-information-control) + [workaround](https://uploadcare.com/docs/mutability/))
* Download static files for scrsets ([webpack](https://github.com/uploadcare/uploadcare-loader))
* Substitute DB with arbitrary metadata ([metadata](https://uploadcare.com/docs/file-metadata/))
* Prepare OG pictures with text ([text overlays](https://uploadcare.com/docs/transformations/image/overlay/#overlay-text))
* Scrap pictures from the web ([from url](https://uploadcare.com/docs/uploading-files/#from-url))
* Make decisions based on files info ([analysis](https://uploadcare.com/docs/file-analysis/) + [webhooks](https://uploadcare.com/docs/webhooks/))
* Weird file conversions ([file coversion](https://uploadcare.com/docs/transformations/document-conversion/#document-file-formats))
* Process and save ([copy remotely](https://uploadcare.com/docs/managing-files/#copy))
* Check for duplicates ([phash](https://uploadcare.com/docs/cdn-operations/#operation-phash))
* Prepare a bunch of files for download ([archive](https://uploadcare.com/docs/cdn-operations/#get-as-archive))
* No-code automate uploads ([Zapier](https://uploadcare.com/docs/integrations/zapier/), [Make](https://www.make.com/en/integrations/uploadcare?utm_source=uploadcare&utm_medium=partner&utm_campaign=uploadcare-partner-program), [Integrately](https://uploadcare.com/docs/integrations/integrately/))
* Do something and don’t store files after it ([storing](https://uploadcare.com/docs/uploads/storage/#file-storing-behavior))

## Demo app

We've developed a demo app that showcases most of the features. You can install [pyuploadcare-example](https://github.com/uploadcare/pyuploadcare-example) using Docker or without it. You can use it as a reference or even base your project on it.

## Useful links

[Uploadcare documentation](https://uploadcare.com/docs/)  
[File Uploader](https://uploadcare.com/docs/file-uploader/)  
[Upload API reference](https://uploadcare.com/api-refs/upload-api/)  
[REST API reference](https://uploadcare.com/api-refs/rest-api/)  
[URL API reference](https://uploadcare.com/api-refs/url-api/)  
[Contributing guide](https://github.com/uploadcare/.github/blob/master/CONTRIBUTING.md)  
[Security policy](https://github.com/uploadcare/uploadcare-swift/security/policy)  
[Support](https://github.com/uploadcare/.github/blob/master/SUPPORT.md)  
