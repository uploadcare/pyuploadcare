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
        'secret': '***'
    }

If you don't want to use hosted assets (from static.uploadcare.com) you
must add 'pyuploadcare.dj' to INSTALLED_APPS setting and add 

    PYUPLOADCARE_USE_HOSTED_ASSETS = False

somewhere in the settings file.

You're all set now!

Adding a UploadCare file field to your model is really simple. Like that:

### models.py

    from django.db import models

    from pyuploadcare.dj import FileField

    class Photo(models.Model):
        title = models.CharField(max_length=255)
        photo = FileField()

`FileField` doesn't require any arguments, file paths or whatever. It **just works**. That's the point of it all.

It look nice in the admin interface

![Admin page](http://f.cl.ly/items/1v120O3h2W462o3T323F/Screen%20Shot%202011-11-04%20at%202.03.32%20PM.png)

### Using it

It's really simple, just use your UploadCare-enabled models as any other models:

    for p in Photo.objects.all():

        # p.photo contains pyuploadcare.file.File object

        print p.photo.url()

        print p.photo.resized(200, 400) # returns the url of resized version of the image
        print p.photo.resized(height=400)
        print p.photo.resized(150, 150, crop=True)

### Using it in templates

To make your life easier, UploadCare file objects understand some 'magic' properties.

    {{ p.photo.resized_120x200_crop }}
    {{ p.photo.resized_120 }}
    {{ p.photo.resized_x120 }}
    {{ p.photo.resized_600x120 }}

These are most useful in Django templates, which are somewhat limited in calling functions with arguments.

[1]: http://uploadcare.com/
[2]: https://groups.google.com/group/uploadcare-testing
