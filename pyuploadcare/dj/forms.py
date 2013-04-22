# coding: utf-8
from django.forms import Field, TextInput

from .. import conf
from . import conf as dj_conf


class FileWidget(TextInput):

    input_type = 'hidden'

    class Media:
        js = (dj_conf.UPLOADCARE_JS,)

    def __init__(self, attrs=None):
        default_attrs = {
            'role': 'uploadcare-uploader',
            'data-public-key': conf.pub_key,
        }

        if dj_conf.UPLOAD_BASE_URL is not None:
            default_attrs['data-upload-base-url'] = dj_conf.UPLOAD_BASE_URL

        if attrs is not None:
            default_attrs.update(attrs)

        super(FileWidget, self).__init__(default_attrs)

    def render(self, name, value, attrs):
        return super(FileWidget, self).render(name, value, attrs)


class FileField(Field):

    widget = FileWidget


class ImageField(Field):

    widget = FileWidget

    def __init__(self, manual_crop=None, *args, **kwargs):
        self.manual_crop = manual_crop
        super(ImageField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = {'data-images-only': ''}
        if self.manual_crop is not None:
            attrs['data-crop'] = self.manual_crop
        return attrs


class FileGroupField(Field):

    widget = FileWidget

    def widget_attrs(self, widget):
        attrs = {'data-multiple': ''}
        return attrs


class ImageGroupField(Field):

    widget = FileWidget

    def widget_attrs(self, widget):
        attrs = {'data-multiple': '', 'data-images-only': ''}
        return attrs
