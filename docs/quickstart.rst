.. _quickstart:

==========
Quickstart
==========

This page gives a good introduction in how to get started with PyUploadcare.
This assumes you have already installed PyUploadcare. If you do not,
head over to the :ref:`Installation <install>` section.

.. warning:: Keep in mind that Uploadcare signature authentication will fail
   if computer clock is not synchronized.

.. _quickstart-api-keys-ref:

Get API Keys
------------

First of all, you'll need API keys: public and private. You can get them
at the `Uploadcare`_ website. If you don't have an account yet, you can use
demo keys, as in example. However, the files on demo account are regularly
deleted, so create an account as soon as Uploadcare catches your fancy.

.. _quickstart-django-ref:

How to use it with Django?
--------------------------

Assume you have a Django project with *gallery* app.

Application Setup
~~~~~~~~~~~~~~~~~

Add ``pyuploadcare.dj`` into ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...
        'pyuploadcare.dj',

        'gallery',
    )

As soon as you :ref:`got your API keys <quickstart-api-keys-ref>`, add them
to your Django settings file:

.. code-block:: python

    UPLOADCARE = {
        'pub_key': 'demopublickey',
        'secret': 'demoprivatekey',
    }

Uploadcare image field adding to your ``gallery/models.py`` is really simple.
Like that:

.. code-block:: python

    from django.db import models

    from pyuploadcare.dj import ImageField


    class Photo(models.Model):

        title = models.CharField(max_length=255)
        photo = ImageField()

``ImageField`` doesn't require any arguments, file paths or whatever.
**It just works.** That's the point of it all.
It looks nice in the admin interface as well:

.. image:: http://www.ucarecdn.com/84e614e4-8faf-4090-ba3a-83294715434b/

Obviously, you would want to use Uploadcare field outside an admin.
It's going to work just as well, but, however, you have to remember to add
``{{ form.media }}`` in the ``<head>`` tag of your page:

.. code-block:: django

    {{ form.media }}

    <form action="" method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <input type="submit" value="Save"/>
    </form>

This is a default Django form property which is going to render any scripts
needed for the form to work, in our case – Uploadcare scripts.

Using it in templates
~~~~~~~~~~~~~~~~~~~~~

You can construct url with all effects manually:

.. code-block:: django

    {% for photo in photos %}
        {{ photo.title }}
        {{ photo.photo.cdn_url }}-/resize/400x300/-/effect/flip/-/effect/grayscale/
    {% endfor %}

Refer to `CDN docs`_ for more information.

.. _quickstart-cli-ref:

How to use it in command line?
------------------------------

.. code-block:: console

    $ ucare -h

.. _Uploadcare: https://uploadcare.com
.. _CDN docs: https://uploadcare.com/documentation/cdn/
