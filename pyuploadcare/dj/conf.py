# coding: utf-8
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .. import conf


if not hasattr(settings, u'UPLOADCARE'):
    raise ImproperlyConfigured(u'UPLOADCARE setting must be set')

if u'pub_key' not in settings.UPLOADCARE:
    raise ImproperlyConfigured(u'UPLOADCARE setting must have pub_key')

if u'secret' not in settings.UPLOADCARE:
    raise ImproperlyConfigured(u'UPLOADCARE setting must have secret')

conf.pub_key = settings.UPLOADCARE[u'pub_key']
conf.secret = settings.UPLOADCARE[u'secret']


widget_version = settings.UPLOADCARE.get(u'widget_version', u'0.8')

hosted_url = u'https://ucarecdn.com/widget/{version}/uploadcare/uploadcare-{version}.min.js'.format(
    version=widget_version)
local_url = u'uploadcare/assets/uploaders/uploadcare-{version}.min.js'.format(
    version=widget_version)

use_hosted_assets = getattr(settings, u'PYUPLOADCARE_USE_HOSTED_ASSETS', True)

if use_hosted_assets:
    UPLOADCARE_JS = hosted_url
else:
    UPLOADCARE_JS = getattr(settings, u'PYUPLOADCARE_WIDGET_URL', local_url)

AVAIL_ASSET_LANG = (u'en', u'ru', u'pl')
UPLOAD_BASE_URL = getattr(settings, u'PYUPLOADCARE_UPLOAD_BASE_URL', None)
