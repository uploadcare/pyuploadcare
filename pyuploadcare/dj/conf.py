#TODO: make this compatible with django-appconf

from django.conf import settings


widget_version = '0.0.1'

hosted_url = 'http://fastatic.uploadcare.com/widget/%(version)s/uploadcare-%(version)s.line.%%(lang)s.js' % {
    'version': widget_version}
local_url = 'uploadcare/assets/uploaders/uploadcare-%(version)s.line.%%(lang)s.js' % {
    'version': widget_version}

use_hosted_assets = getattr(settings, 'PYUPLOADCARE_USE_HOSTED_ASSETS', True)

if use_hosted_assets:
    UPLOADCARE_JS = hosted_url
else:
    UPLOADCARE_JS = getattr(settings, 'PYUPLOADCARE_WIDGET_URL', local_url)

AVAIL_ASSET_LANG = ('en', 'ru', 'pl')
UPLOAD_BASE_URL = getattr(settings, 'PYUPLOADCARE_UPLOAD_BASE_URL', None)
