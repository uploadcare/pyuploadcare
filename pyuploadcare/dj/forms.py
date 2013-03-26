from django.forms import Field, TextInput
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pyuploadcare.dj import conf
from pyuploadcare.dj import UploadCare


class FileWidget(TextInput):
    input_type = 'hidden'

    class Media:
        js = (conf.UPLOADCARE_JS,)

    def __init__(self, attrs=None):
        default_attrs = {
            'role': 'uploadcare-uploader',
            'data-public-key': UploadCare().pub_key,
        }

        if conf.UPLOAD_BASE_URL is not None:
            default_attrs['data-upload-base-url'] = conf.UPLOAD_BASE_URL

        if attrs is not None:
            default_attrs.update(attrs)

        super(FileWidget, self).__init__(default_attrs)

    def render(self, name, value, attrs):
        return super(FileWidget, self).render(name, value, attrs)


class FileField(Field):
    widget = FileWidget


class ImageField(Field):

    widget = FileWidget

    def __init__(self, crop_tool=None, *args, **kwargs):
        self.crop_tool = crop_tool
        super(ImageField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = {'data-images-only': ''}
        if self.crop_tool is not None:
            attrs['data-crop'] = self.crop_tool
        return attrs
