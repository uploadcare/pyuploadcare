from django.conf import settings

import pyuploadcare

def UploadCare(**kwargs):
    kws = dict(settings.UPLOADCARE)
    kws.update(kwargs)

    return pyuploadcare.UploadCare(**kws)

from pyuploadcare.dj.models import FileField


# making South happy

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^pyuploadcare\.dj\."])
except ImportError, e:
    pass
