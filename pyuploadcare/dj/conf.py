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


widget_version = settings.UPLOADCARE.get('widget_version', '0.8')

hosted_url = 'https://ucarecdn.com/widget/{version}/uploadcare/uploadcare-{version}.min.js'.format(
    version=widget_version)
local_url = 'uploadcare/assets/uploaders/uploadcare-{version}.min.js'.format(
    version=widget_version)

use_hosted_assets = getattr(settings, 'PYUPLOADCARE_USE_HOSTED_ASSETS', True)

if use_hosted_assets:
    UPLOADCARE_JS = hosted_url
else:
    UPLOADCARE_JS = getattr(settings, 'PYUPLOADCARE_WIDGET_URL', local_url)

AVAIL_ASSET_LANG = ('en', 'ru', 'pl')
UPLOAD_BASE_URL = getattr(settings, 'PYUPLOADCARE_UPLOAD_BASE_URL', None)
