# PyUploadCare: a Python module for UploadCare

This consists in API interface for [UploadCare][1], and a couple of Django goodies.

To install it, just run

    pip install pyuploadcare

(or `easy_install pyuploadcare` if you're into vintage)

## How to use it with Django?

First of all, you'll need API keys: public and private. You can get them at [the UploadCare website][1]. Currently it requires an invitation code to register, please request an access to [uploadcare-testing user group][2] and find it there.

As soon as you get your API keys, add them to your Django settings file:

### settings.py

    UPLOADCARE = {
        'pub_key': '***',
        'secret': '***',
        'api_version': '0.2',
    }

If you don't want to use hosted assets (from fastatic.uploadcare.com) you
should add 'pyuploadcare.dj' to INSTALLED_APPS setting and add

    PYUPLOADCARE_USE_HOSTED_ASSETS = False


to django settings file. (Kudos to [Sławek Ehlert][3] for the feature!)

[3]: https://github.com/slafs

If you want to provide custom url for widget, you should add 'pyuploadcare.dj'
to INSTALLED_APPS setting and add

    PYUPLOADCARE_USE_HOSTED_ASSETS = False
    PYUPLOADCARE_WIDGET_URL = 'http://path.to.asset'
    # or
    PYUPLOADCARE_WIDGET_URL = 'http://path.to.%(lang)s.asset.'


to django settings file. 'lang' placeholder will be substituted with current
locale name from supported list ('en', 'pl', 'ru') or 'en'.

UploadCare widget will use default upload handler url, unless you specify
PYUPLOADCARE_UPLOAD_BASE_URL django settings

    PYUPLOADCARE_UPLOAD_BASE_URL = 'http://path.to.your.upload.handler'


You're all set now!

Adding a UploadCare file field to your model is really simple. Like that:

### models.py

    from django.db import models

    from pyuploadcare.dj import FileField


    class Photo(models.Model):
        title = models.CharField(max_length=255)
        photo = FileField()

`FileField` doesn't require any arguments, file paths or whatever. It **just works**. That's the point of it all.

It looks nice in the admin interface

![Admin page](http://f.cl.ly/items/1v120O3h2W462o3T323F/Screen%20Shot%202011-11-04%20at%202.03.32%20PM.png)

### Using it

It's really simple, just use your UploadCare-enabled models as any other models:

    for p in Photo.objects.all():

        # p.photo contains pyuploadcare.file.File object

        print p.photo.cdn_url

        print p.photo.resized(200, 400) # returns the url of resized version of the image
        print p.photo.resized(height=400)
        print p.photo.cropped(150, 150)

### Using it in templates

To make your life easier, UploadCare file objects understand some 'magic' properties.

    {{ p.photo.cropped_120x200 }}
    {{ p.photo.resized_120 }}
    {{ p.photo.resized_x120 }}
    {{ p.photo.resized_600x120 }}

These are most useful in Django templates, which are somewhat limited in calling functions with arguments.
Or you can contruct url manually:

    {{ p.photo.cdn_url }}-/resize/400x300/-/effect/flip/-/effect/grayscale/


[1]: http://uploadcare.com/
[2]: https://groups.google.com/group/uploadcare-testing
