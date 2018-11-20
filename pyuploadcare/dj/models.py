# coding: utf-8
from __future__ import unicode_literals
import re

from django.db import models
from django.core.exceptions import ValidationError
import six

from . import forms
from .subclassing import SubfieldBase
from ..exceptions import InvalidRequestError
from ..api_resources import File, FileGroup


class FileField(six.with_metaclass(SubfieldBase, models.Field)):
    """Django model field that stores uploaded file as Uploadcare CDN url.
    """

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        if value is None or value == '':
            return value

        if isinstance(value, File):
            return value

        if not isinstance(value, six.string_types):
            raise ValidationError(
                'Invalid value for a field: string was expected'
            )

        try:
            return File(value)
        except InvalidRequestError as exc:
            raise ValidationError(
                'Invalid value for a field: {exc}'.format(exc=exc)
            )

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        else:
            return value.cdn_url

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        kwargs['form_class'] = forms.FileField
        return super(FileField, self).formfield(**kwargs)

    def validate(self, value, model_instance):
        super(FileField, self).validate(value, model_instance)

        if value:
            try:
                # Hack for receiving information about file and if error
                # happens (e.g. file not found) we catching it and
                # re-raise as ValidationError.
                value.info()
            except InvalidRequestError as exc:
                raise ValidationError(
                    'The file could not be found in your Uploadcare project. '
                    'Underlying error: "{exc}".'.format(exc=exc),
                    code='invalid_url')

    def clean(self, value, model_instance):
        cleaned_value = super(FileField, self).clean(value, model_instance)
        if cleaned_value and not cleaned_value.is_stored():
            cleaned_value.store()
        return cleaned_value


pattern_of_crop = re.compile('''
    ^
    (
        disabled| # "disabled"
        | # empty string
        \d+:\d+| # "2:3"
        \d+x\d+| # "200x300"
        \d+x\d+\ upscale| # "200x300 upscale"
        \d+x\d+\ minimum  # "200x300 minimum"
    )
    $
''', re.VERBOSE)


class ImageField(FileField):
    """Django model field that stores uploaded image as Uploadcare CDN url.

    It supports manual crop as well. *manual_crop* can be set to one
    of the following values:

    - ``None``, ``"disabled"`` — crop disabled;
    - ``""`` — crop is enabled and the user will be able to select any area
      on an image;
    - ``"2:3"`` — user will be able to select an area with aspect ratio *2:3*;
    - ``"200x300"`` — same as previous, but if the selected area is bigger
      than *200x300*, it will be scaled down to these dimensions;
    - ``"200x300 upscale"`` — same as previous, but the selected area
      will be scaled even if it is smaller than the specified size.

    """

    def __init__(self, manual_crop=None, *args, **kwargs):
        is_crop_valid = (
            isinstance(manual_crop, six.string_types) and
            all([pattern_of_crop.match(part) for part in manual_crop.split(',')])
        )
        if not (manual_crop is None or is_crop_valid):
            raise ValidationError('Invalid manual crop value')

        self.manual_crop = manual_crop
        super(ImageField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['manual_crop'] = self.manual_crop
        kwargs['form_class'] = forms.ImageField

        return models.Field.formfield(self, **kwargs)


class FileGroupField(six.with_metaclass(SubfieldBase, models.Field)):
    """Django model field that stores uploaded file group as Uploadcare CDN url.

    It provides multiple file uploading.

    """

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        if value is None or value == '':
            return value

        if isinstance(value, FileGroup):
            return value

        if not isinstance(value, six.string_types):
            raise ValidationError(
                'Invalid value for a field: string was expected'
            )

        try:
            return FileGroup(value)
        except InvalidRequestError as exc:
            raise ValidationError(
                'Invalid value for a field: {exc}'.format(exc=exc)
            )

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        else:
            return value.cdn_url

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        kwargs['form_class'] = forms.FileGroupField

        return models.Field.formfield(self, **kwargs)

    def clean(self, value, model_instance):
        cleaned_value = super(FileGroupField, self).clean(value, model_instance)
        if cleaned_value:
            cleaned_value.store()
        return cleaned_value


class ImageGroupField(FileGroupField):
    """Django model field that stores uploaded image group as Uploadcare CDN url.

    It provides multiple image uploading.

    """

    def formfield(self, **kwargs):
        kwargs['form_class'] = forms.ImageGroupField

        return models.Field.formfield(self, **kwargs)
