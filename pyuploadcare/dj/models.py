from django.db import models
from django.core.exceptions import ValidationError

from pyuploadcare.dj import forms, UploadCare
from pyuploadcare.file import File


class FileField(models.Field):
    __metaclass__ = models.SubfieldBase

    description = "UploadCare file id/URI with cached data"

    def __init__(self, *args, **kwargs):
        super(FileField, self).__init__(*args, **kwargs)


    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        if not value:
            return None
            
        if isinstance(value, basestring):
            return UploadCare().file(value)        

        if isinstance(value, File):
            return value
        
        raise ValidationError('Invalid value for a field')

    def get_prep_value(self, value):
        return value.serialize()

    def get_db_prep_save(self, value):
        if value:
            value.keep()
            return value.serialize()

    def value_to_string(self, obj):
        assert False

    def formfield(self, **kwargs):
        defaults = {'widget': forms.FileWidget, 'form_class': forms.FileField}
        defaults.update(kwargs)

        # yay for super!
        return super(FileField, self).formfield(**defaults)
