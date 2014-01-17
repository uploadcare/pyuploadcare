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


widget_version = settings.UPLOADCARE.get('widget_version', '0.17.1')

hosted_url = 'https://ucarecdn.com/widget/{version}/uploadcare/uploadcare-{version}.min.js'.format(
    version=widget_version)
local_url = 'uploadcare/uploadcare-{version}.min.js'.format(
    version=widget_version)

use_hosted_assets = settings.UPLOADCARE.get(
    'use_hosted_assets',
    getattr(settings, 'PYUPLOADCARE_USE_HOSTED_ASSETS', True)
)

if use_hosted_assets:
    uploadcare_js = hosted_url
else:
    uploadcare_js = settings.UPLOADCARE.get(
        'widget_url',
        getattr(settings, 'PYUPLOADCARE_WIDGET_URL', local_url)
    )

upload_base_url = settings.UPLOADCARE.get(
    'upload_base_url',
    getattr(settings, 'PYUPLOADCARE_UPLOAD_BASE_URL', None)
)
