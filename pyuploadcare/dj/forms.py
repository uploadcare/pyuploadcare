# coding: utf-8
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.forms import Field, TextInput

from .. import conf
from ..exceptions import InvalidRequestError
from ..api_resources import File, FileGroup
from . import conf as dj_conf


class FileWidget(TextInput):
    """Django form widget that sets up Uploadcare Widget.

    It adds js and hidden input with basic Widget's params, e.g.
    *data-public-key*.

    """

    input_type = 'hidden'
    is_hidden = False

    class Media:
        js = (dj_conf.uploadcare_js,)

    def __init__(self, attrs=None):
        default_attrs = {
            'role': 'uploadcare-uploader',
            'data-public-key': conf.pub_key,
        }

        if conf.user_agent_extension is not None:
            default_attrs['data-integration'] = conf.user_agent_extension

        if dj_conf.upload_base_url is not None:
            default_attrs['data-url-base'] = dj_conf.upload_base_url

        if attrs is not None:
            default_attrs.update(attrs)

        super(FileWidget, self).__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        return super(FileWidget, self).render(name, value, attrs, renderer)


class FileField(Field):
    """Django form field that uses ``FileWidget`` with default arguments.

    It always returns URL.

    """

    widget = FileWidget

    def to_python(self, value):
        if value is None or value == '':
            return value

        try:
            return File(value).cdn_url
        except InvalidRequestError as exc:
            raise ValidationError(
                'Invalid value for a field: {exc}'.format(exc=exc)
            )

    def widget_attrs(self, widget):
        attrs = {}
        if not self.required:
            attrs['data-clearable'] = ''
        return attrs


class ImageField(FileField):
    """Django form field that sets up ``FileWidget`` to work with images.
    """

    def __init__(self, manual_crop=None, *args, **kwargs):
        self.manual_crop = manual_crop
        super(ImageField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(ImageField, self).widget_attrs(widget)
        attrs['data-images-only'] = ''
        if self.manual_crop is not None:
            attrs['data-crop'] = self.manual_crop
        return attrs


class FileGroupField(Field):
    """Django form field that sets up ``FileWidget`` in multiupload mode.
    """

    widget = FileWidget

    def to_python(self, value):
        if value is None or value == '':
            return value

        try:
            return FileGroup(value).cdn_url
        except InvalidRequestError as exc:
            raise ValidationError(
                'Invalid value for a field: {exc}'.format(exc=exc)
            )

    def widget_attrs(self, widget):
        attrs = {'data-multiple': ''}
        if not self.required:
            attrs['data-clearable'] = ''
        return attrs


class ImageGroupField(FileGroupField):
    """Django form field that sets up ``FileWidget`` in image multiupload mode.
    """

    def widget_attrs(self, widget):
        attrs = super(ImageGroupField, self).widget_attrs(widget)
        attrs['data-images-only'] = ''
        return attrs
