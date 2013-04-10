=============================================
PyUploadcare: a Python library for Uploadcare
=============================================

The most importang thing for us at `Uploadcare`_ is to make file uploading on
the web really easy. Everyone is used to the routine work, related to allowing
users upload their userpics or attach resumes: from installing image processing
libraries to creating folder with right permissions to ensuring the server
never goes down or out of space to enabling CDN. Feature like ability to simply
use a picture from Facebook or manual cropping are much more burdensome,
hence rare. Uploadcare's goal is to change the status quo.

This library consists of an API interface for `Uploadcare`_ and a couple
of Django goodies.

A simple Uploadcare ``FileField`` can be added to an existing Django project
in just a couple of :ref:`simple steps <quickstart>`. As a result, your users
are going to be able to see the progress of the upload, choose files from
Google Drive or Instagram, and edit form while files are uploading
asynchornously.

Contents:

.. toctree::
   :maxdepth: 2

   install
   quickstart
   django-widget
   cli
   deprecated

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api/core
   api/django-widget
   api/cli

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Uploadcare: https://uploadcare.com
