from django.conf import settings

import pyuploadcare

def UploadCare(**kwargs):
    kws = dict(settings.UPLOADCARE)
    kws.update(kwargs)

    return pyuploadcare.UploadCare(**kws)

from pyuploadcare.dj.models import FileField
