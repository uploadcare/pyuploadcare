# coding: utf-8
from pyuploadcare.dj.models import (
    FileField, ImageField, FileGroupField, ImageGroupField,
)


# making South happy
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^pyuploadcare\.dj\."])
except ImportError:
    pass
