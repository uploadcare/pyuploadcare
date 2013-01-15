# PyUploadcare: a Python module for Uploadcare

This consists in API interface for [Uploadcare][1], and a couple of Django goodies.

To install it, just run

    pip install pyuploadcare

(or `easy_install pyuploadcare` if you're into vintage)

You can use `pyuploadcare` now:

    >>> import pyuploadcare
    >>> pyuploadcare.UploadCare
    <class 'pyuploadcare.UploadCare'>

You can also use our console utility, `ucare`:

    $ ucare -h

## How to use it with Django?

First of all, you'll need API keys: public and private. You can get them at [the Uploadcare website][1].

As soon as you get your API keys, add them to your Django settings file:

### settings.py

    UPLOADCARE = {

        # Don't forget to change to real keys when it gets serious!

        'pub_key': 'demopublickey',
        'secret': 'demoprivatekey',
    }

You're all set now!

Adding a Uploadcare file field to your model is really simple. Like that:

### models.py

    from django.db import models

    from pyuploadcare.dj import FileField


    class Photo(models.Model):
        title = models.CharField(max_length=255)
        photo = FileField()

`FileField` doesn't require any arguments, file paths or whatever. It **just works**. That's the point of it all.

It looks nice in the admin interface

![Admin page](https://ucarecdn.com/84e614e4-8faf-4090-ba3a-83294715434b/)

### Using it

It's really simple, just use your Uploadcare-enabled models as any other models:

    for p in Photo.objects.all():

        # p.photo contains pyuploadcare.file.File object

        print p.photo.cdn_url

        print p.photo.resized(200, 400) # returns the url of resized version of the image
        print p.photo.resized(height=400)
        print p.photo.cropped(150, 150)

### Using it in templates

You can contruct url with all effects manually:

    {{ p.photo.cdn_url }}-/resize/400x300/-/effect/flip/-/effect/grayscale/

Refer to [CDN docs][5] for more information.


### Time settings

Keep in mind that Uploadcare authentication will fail if computer clock is not synchronized.


### Advanced settings

If you don't want to use hosted assets (from fastatic.uploadcare.com) you
should add 'pyuploadcare.dj' to INSTALLED_APPS setting and add

    PYUPLOADCARE_USE_HOSTED_ASSETS = False


to django settings file. (Kudos to [Sławek Ehlert][3] for the feature!)

[3]: https://github.com/slafs

If you want to provide custom url for widget, you should add 'pyuploadcare.dj'
to INSTALLED_APPS setting and add

    PYUPLOADCARE_USE_HOSTED_ASSETS = False
    PYUPLOADCARE_WIDGET_URL = 'http://path.to.asset'


to django settings file.

Uploadcare widget will use default upload handler url, unless you specify
PYUPLOADCARE_UPLOAD_BASE_URL django settings

    PYUPLOADCARE_UPLOAD_BASE_URL = 'http://path.to.your.upload.handler'


[1]: https://uploadcare.com/
[5]: https://uploadcare.com/documentation/reference/basic/cdn/
