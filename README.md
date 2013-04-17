# PyUploadcare: a Python library for Uploadcare

[![Build Status](https://travis-ci.org/uploadcare/pyuploadcare.png?branch=master)](https://travis-ci.org/uploadcare/pyuploadcare)

The most important thing for us at [Uploadcare][1] is to make file uploading on
the web really easy. Everyone is used to the routine work, related to allowing
users upload their userpics or attach resumes: from installing image processing
libraries to creating folder with right permissions to ensuring the server
never goes down or out of space to enabling CDN. Feature like ability to simply
use a picture from Facebook or manual cropping are much more burdensome,
hence rare. Uploadcare's goal is to change the status quo.

This library consists of an API interface for [Uploadcare][1] and a couple
of Django goodies.

A simple Uploadcare ``ImageField`` can be added to an existing Django project
in just a couple of [simple steps][2]. As a result, your users
are going to be able to see the progress of the upload, choose files from
Google Drive or Instagram, and edit form while files are uploading
asynchornously.

    from django.db import models

    from pyuploadcare.dj import ImageField


    class Candidate(models.Model):

        photo = ImageField(blank=True, manual_crop="")

![ImageField with crop tool](https://ucarecdn.com/93b254a3-8c7a-4533-8c01-a946449196cb/-/preview/manual_crop.png)

## Features

- Django widget with useful manual crop and multiupload;
- *ucare* console utility;
- hosted assets (Kudos to [Sławek Ehlert][3]!).

## Installation

To install it, just run:

    $ pip install pyuploadcare

or, if you're into vintage:

    $ easy_install pyuploadcare

[1]: https://uploadcare.com/
[2]: https://pyuploadcare.readthedocs.org/en/latest/quickstart.html
[3]: https://github.com/slafs

## Testing

Besides the [Travis CI](https://travis-ci.org/uploadcare/pyuploadcare) we use tox.
In order to run tests just:

    $ pip install tox
    $ tox
