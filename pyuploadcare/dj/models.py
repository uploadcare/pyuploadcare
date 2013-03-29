from django.db import models
from django.core.exceptions import ValidationError

from pyuploadcare.dj import forms, UploadCare
from pyuploadcare.exceptions import InvalidRequestError
from pyuploadcare.file import File


class FileField(models.Field):
    __metaclass__ = models.SubfieldBase

    description = "UploadCare file id/URI with cached data"

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, File):
            return value

        if not isinstance(value, basestring):
            raise ValidationError(
                u'Invalid value for a field: string was expected'
            )

        try:
            return UploadCare().file(value)
        except InvalidRequestError as exc:
            raise ValidationError(
                u'Invalid value for a field: {exc}'.format(exc=exc)
            )

    def get_prep_value(self, value):
        return value.serialize()

    def get_db_prep_save(self, value, connection=None):
        if value:
            value.store()
            return value.serialize()

    def value_to_string(self, obj):
        assert False

    def formfield(self, **kwargs):
        defaults = {'widget': forms.FileWidget, 'form_class': forms.FileField}
        defaults.update(kwargs)

        # yay for super!
        return super(FileField, self).formfield(**defaults)
