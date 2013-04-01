import re

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
        if value is None or value == '':
            return value

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
        return value.serialize() if value else value

    def get_db_prep_save(self, value, connection=None):
        if value:
            value.store()
        return super(FileField, self).get_db_prep_save(value, connection)

    def value_to_string(self, obj):
        assert False

    def formfield(self, **kwargs):
        defaults = {'widget': forms.FileWidget, 'form_class': forms.FileField}
        defaults.update(kwargs)

        # yay for super!
        return super(FileField, self).formfield(**defaults)


pattern_of_crop = re.compile(u'''
    ^
    (
        disabled| # "disabled"
        | # empty string
        \d+:\d+| # "2:3"
        \d+x\d+| # "200x300"
        \d+x\d+\ upscale # "200x300 upscale"
    )
    $
''', re.VERBOSE)


class ImageField(FileField):

    def __init__(self, manual_crop=None, *args, **kwargs):
        is_crop_valid = (
            isinstance(manual_crop, basestring) and
            pattern_of_crop.match(manual_crop)
        )
        if not (manual_crop is None or is_crop_valid):
            raise ValidationError('Invalid manual crop value')

        self.manual_crop = manual_crop
        super(ImageField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'manual_crop': self.manual_crop}
        defaults.update(kwargs)

        return super(ImageField, self).formfield(form_class=forms.ImageField,
                                                 **defaults)
