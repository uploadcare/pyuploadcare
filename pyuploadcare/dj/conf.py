# coding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .. import conf


if not hasattr(settings, 'UPLOADCARE'):
    raise ImproperlyConfigured('UPLOADCARE setting must be set')

if 'pub_key' not in settings.UPLOADCARE:
    raise ImproperlyConfigured('UPLOADCARE setting must have pub_key')

if 'secret' not in settings.UPLOADCARE:
    raise ImproperlyConfigured('UPLOADCARE setting must have secret')

conf.pub_key = settings.UPLOADCARE['pub_key']
conf.secret = settings.UPLOADCARE['secret']


widget_version = settings.UPLOADCARE.get('widget_version', '0.8.1.2')

hosted_url = 'https://ucarecdn.com/widget/{version}/uploadcare/uploadcare-{version}.min.js'.format(
    version=widget_version)
local_url = 'uploadcare/assets/uploaders/uploadcare-{version}.min.js'.format(
    version=widget_version)

if 'use_hosted_assets' in settings.UPLOADCARE:
    use_hosted_assets = getattr(settings.UPLOADCARE, 'use_hosted_assets', True)
else:
    # Deprecated.
    use_hosted_assets = getattr(settings, 'PYUPLOADCARE_USE_HOSTED_ASSETS', True)

if use_hosted_assets:
    UPLOADCARE_JS = hosted_url
else:
    if 'widget_url' in settings.UPLOADCARE:
        UPLOADCARE_JS = getattr(settings.UPLOADCARE, 'widget_url', local_url)
    else:
        # Deprecated.
        UPLOADCARE_JS = getattr(settings, 'PYUPLOADCARE_WIDGET_URL', local_url)

if 'upload_base_url' in settings.UPLOADCARE:
    UPLOAD_BASE_URL = getattr(settings.UPLOADCARE, 'upload_base_url', None)
else:
    # Deprecated.
    UPLOAD_BASE_URL = getattr(settings, 'PYUPLOADCARE_UPLOAD_BASE_URL', None)
