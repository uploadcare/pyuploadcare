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
        html = super(FileWidget, self).render(name, value, attrs)

        if value:
            if isinstance(value, basestring):
                value = UploadCare().file(value)

            if value.url:
                fname = '<a href="{0}">{1}</a>'.format(value.url, value.filename)
            else:
                fname = '{0} ({1})'.format(value.filename, _('unavail.'))

            description = '<p>{0}: {1}</p>'.format(_('File'), fname)

            html = mark_safe(html + description)

        return html


class FileField(Field):
    widget = FileWidget
