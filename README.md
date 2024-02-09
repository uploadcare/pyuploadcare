<p align="center">
  <a href="https://uploadcare.com/?ref=github-readme">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset="https://ucarecdn.com/1b4714cd-53be-447b-bbde-e061f1e5a22f/logosafespacetransparent.svg">
      <source media="(prefers-color-scheme: dark)" srcset="https://ucarecdn.com/3b610a0a-780c-4750-a8b4-3bf4a8c90389/logotransparentinverted.svg">
      <img width=250 alt="Uploadcare logo" src="https://ucarecdn.com/1b4714cd-53be-447b-bbde-e061f1e5a22f/logosafespacetransparent.svg">
    </picture>
  </a>
</p>
<p align="center">
  <a href="https://pyuploadcare.readthedocs.io/en/latest/">Package Docs</a> • 
  <a href="https://uploadcare.com/docs/">Uploadcare Docs</a> • 
  <a href="https://uploadcare.com/api-refs/upload-api/">Upload API Reference</a> • 
  <a href="https://uploadcare.com/api-refs/rest-api/">REST API Reference</a> • 
  <a href="https://uploadcare.com/api-refs/url-api/">URL API Reference</a> • 
  <a href="https://uploadcare.com/">Website</a>
</p>

# Python API client for Uploadcare

[![](https://badge.fury.io/py/pyuploadcare.svg)](https://pypi.org/project/pyuploadcare/)
[![](https://github.com/uploadcare/pyuploadcare/actions/workflows/test.yml/badge.svg)](https://github.com/uploadcare/pyuploadcare/actions?query=branch%3Amain+workflow%3ATests++)
[![](https://readthedocs.org/projects/pyuploadcare/badge/?version=latest)](https://pyuploadcare.readthedocs.io/)
[![](https://img.shields.io/badge/tech-stack-0690fa.svg?style=flat)](https://stackshare.io/uploadcare)

Build file handling in minutes. Upload or accept UGC, store, transform, optimize, and deliver images, videos, and documents to billions of users.

* [Features](#features)
* [Documentation](#documentation)
* [Requirements and installation](#requirements-and-installation)
* [Usage example](#usage-example)
* [Use cases](#use-cases)
* [Demo app (Docker)](#demo-app)
* [Suggestions and questions](#suggestions-and-questions)

## Features

This library consists of the APIs interface and a couple of Django goodies, 100% covering [Upload](https://uploadcare.com/api-refs/upload-api/), [REST](https://uploadcare.com/api-refs/rest-api/) and [URL](https://uploadcare.com/api-refs/url-api/) Uploadcare APIs.

* Enable obsessively friendly [file uploads](http://uploadcare.com/products/file-uploader/)
* Manage stored files RESTfully: from malware detection to file conversion
* [Optimize and process images on the fly](https://uploadcare.com/cdn/image-cdn/) right before delivery time

<!-- Enable obsessively friendly file uploads:
* Built-in File Uploader
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
* Proxy to fetch and deliver remote files -->

## Documentation

Detailed specification of this library is available [on RTD](https://pyuploadcare.readthedocs.io/en/latest/).

Please note that this package uses Uploadcare [API keys](https://app.uploadcare.com/projects/-/api-keys) and is intended to be used in server-side code only.

## Requirements and installation

* Python 3.8, 3.9, 3.10, 3.11, 3.12

To use pyuploadcare with Python 3.6 or 3.7 please install `pyuploadcare < 5.0`.

To use pyuploadcare with Python 2.7 please install `pyuploadcare < 3.0`.

Django compatibility:

| Py/Dj | 2.2 | 3.0 | 3.1 | 3.2 | 4.0 | 4.1 | 4.2 | 5.0 |
| ----- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3.8   | X   | X   | X   | X   | X   | X   | X   |     |
| 3.9   | X   | X   | X   | X   | X   | X   | X   |     |
| 3.10  |     |     |     | X   | X   | X   | X   | X   |
| 3.11  |     |     |     |     |     | X   | X   | X   |
| 3.12  |     |     |     |     |     |     | X   | X   |

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

<!-- TODO: The idea of this example is to show how upload and deliver an image -->

<!-- TODO: Update it with "and deliver an image" -->
Let's add [File Uploader](https://uploadcare.com/docs/file-uploader/) to an existing Django project.

After package [installation](#requirements-and-installation), you’ll need API keys: public and secret. Get them in [Uploadcare dashboard](https://app.uploadcare.com/projects/-/api-keys). If you don’t have an account yet, you can use demo keys, as in example. However, the files on demo account are regularly removed, so create an account as soon as Uploadcare catches your fancy.

Assume you have a Django project with gallery app.

Add `pyuploadcare.dj` into `INSTALLED_APPS`:

```python
INSTALLED_APPS = (
    # ...
    'pyuploadcare.dj',

    'gallery',
)
```
Add API keys to your Django settings file:

```python
UPLOADCARE = {
    'pub_key': 'demopublickey',
    'secret': 'demoprivatekey',
}
```

Uploadcare image field adding to your `gallery/models.py` is really simple. Like that:

```python
from django.db import models

from pyuploadcare.dj.models import ImageField


class Photo(models.Model):

    title = models.CharField(max_length=255)
    photo = ImageField()
```

`ImageField` doesn’t require any arguments, file paths or whatever. **It just works**. That’s the point of it all. It looks nice in the admin interface as well:

<!-- TODO: Update screenshot -->
![](https://ucarecdn.com/84e614e4-8faf-4090-ba3a-83294715434b/)

Obviously, you would want to use Uploadcare field outside an admin. It’s going to work just as well, but, however, you have to remember to add {{ form.media }} in the <head> tag of your page:

```python
{{ form.media }}

<form action="" method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <input type="submit" value="Save"/>
</form>
```

This is a default Django form property which is going to render any scripts needed for the form to work, in our case — Uploadcare scripts.

<!-- TODO: Update how we get an UUID and pass it further -->
After an image is uploaded, you can deliver it while transforming it on the fly:

```python
{% for photo in photos %}
    {{ photo.title }}
    {{ photo.photo.cdn_url }}-/resize/400x300/-/effect/flip/-/effect/grayscale/
{% endfor %}
```

<!-- TODO: Maybe we should link to the URL builder pyuploadcare docs? -->
(Refer to Uploadcare [image processing docs](https://uploadcare.com/docs/transformations/image/) for more information).

<!-- TODO: Connect this example to the rest of them -->
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

## Testing

To run tests using [Github Actions](https://github.com/uploadcare/pyuploadcare/actions) workflows, but locally, install the [act](https://github.com/nektos/act) utility, and then run it:

```make test_with_github_actions```

This runs the full suite of tests across Python and Django versions.

<!--
## Use cases

In this spreadsheet we also provide links to the [Uploadcare documentation](https://uploadcare.com/docs/) so you can fully understand what our platform enables.
Manual describes a product feature, and code leads to the library code specification.

| Feature                        | Description | Manual                                                                     | Code                                                                                      |
| ------------------------------ | ----------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| _Uploading_                    |             | [_Overview_](https://uploadcare.com/docs/uploads/)                         |                                                                                           |
| Uploading files                |             | [Manual](https://uploadcare.com/docs/uploading-files/)                     | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#uploading-files)       |
| File Uploader                  |             | [Manual](https://uploadcare.com/docs/file-uploader/)                       | [Code](https://pyuploadcare.readthedocs.io/en/latest/django-widget.html)                  |
| Storage options                |             | [Manual](https://uploadcare.com/docs/uploads/storage/)                     | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#store-files)           |
| Signed uploads                 |             | [Manual](https://uploadcare.com/docs/security/secure-uploads/)             | ?                                                                                         |
| File analysis on upload        |             | [Manual](https://uploadcare.com/docs/file-analysis/)                       | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#retrieve-files)        |
| Validation and moderation      |             | [Manual](https://uploadcare.com/docs/moderation/)                          | N/A                                                                                       |
| _File management_              |             | [_Overview_](https://uploadcare.com/docs/start/file-management/)           |                                                                                           |
| Managing files                 |             | [Manual](https://uploadcare.com/docs/managing-files/)                      | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#list-files)            |
| Projects                       |             | [Manual](https://uploadcare.com/docs/start/settings/)                      | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#get-project-info)      |
| Webhook notifications          |             | [Manual](https://uploadcare.com/docs/webhooks/)                            | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#create-webhook)        |
| S3 bucket integration          |             | [Manual](https://uploadcare.com/docs/s3-integration/)                      | N/A                                                                                       |
| Arbitrary file metadata        |             | [Manual](https://uploadcare.com/docs/file-metadata/)                       | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#file-metadata)         |
| Video processing               |             | [Manual](https://uploadcare.com/docs/transformations/video-encoding/)      | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#video-conversion)      |
| Document conversion            |             | [Manual](https://uploadcare.com/docs/transformations/document-conversion/) | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#document-conversion)   |
| Unsafe content detection       |             | [Manual](https://uploadcare.com/docs/unsafe-content/)                      | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#using-addons)          |
| Object recognition             |             | [Manual](https://uploadcare.com/docs/intelligence/object-recognition/)     | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#using-addons)          |
| Malware protection             |             | [Manual](https://uploadcare.com/docs/security/malware-protection/)         | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#using-addons)          |
| _Delivery_                     |             | [_Overview_](https://uploadcare.com/docs/delivery/)                        |                                                                                           |
| On-the-fly operations          |             | [Manual](https://uploadcare.com/docs/cdn-operations/)                      | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#image-transformations) |
| Image optimization             |             | [Manual](https://uploadcare.com/docs/transformations/image/compression/)   | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#image-transformations) |
| Image transformation           |             | [Manual](https://uploadcare.com/docs/transformations/image/)               | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#image-transformations) |
| CDN settings                   |             | [Manual](https://uploadcare.com/docs/delivery/cdn/)                        | N/A                                                                                       |
| Fetch and deliver remote files |             | [Manual](https://uploadcare.com/docs/delivery/proxy/)                      | N/A                                                                                       |
| Signed URLs                    |             | [Manual](https://uploadcare.com/docs/security/secure-delivery/)            | [Code](https://pyuploadcare.readthedocs.io/en/latest/core_api.html#secure-delivery)       |

To help you figure what this library can help you with, we want to showcase some use cases that you can solve with Uploadcare.

Main use cases:
* Accept user-generated content ([upload api](https://uploadcare.com/docs/uploading-files/), [file uploader](https://uploadcare.com/docs/file-uploader/), [upload sources](https://uploadcare.com/docs/upload-sources/))
* Serve responsive images ([optimization](https://uploadcare.com/docs/transformations/image/compression/), [adaptive image SDK](https://uploadcare.com/docs/adaptive-image/), [proxy](https://uploadcare.com/docs/delivery/proxy/), and other [integrations](https://uploadcare.com/docs/integrations/))

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
 -->

## Demo app

We've developed a demo app that showcases most of the features. You can install [pyuploadcare-example](https://github.com/uploadcare/pyuploadcare-example) using Docker or without it. You can use it as a reference or even base your project on it.

## Suggestions and questions

[Contributing guide](https://github.com/uploadcare/.github/blob/master/CONTRIBUTING.md)  
[Security policy](https://github.com/uploadcare/uploadcare-swift/security/policy)  
[Support](https://github.com/uploadcare/.github/blob/master/SUPPORT.md)  
