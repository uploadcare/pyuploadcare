#TODO: make this compatible with django-appconf

from django.conf import settings

USE_HOSTED_ASSETS = getattr(settings, 'PYUPLOADCARE_USE_HOSTED_ASSETS', True)

