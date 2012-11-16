#TODO: make this compatible with django-appconf

from django.conf import settings


widget_version = '0.4.2'

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
