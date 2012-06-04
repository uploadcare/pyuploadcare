from django.forms import Field, TextInput
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, get_language

from pyuploadcare.dj import conf
from pyuploadcare.dj import UploadCare


def get_asset_lang():
    """returns a localized asset url"""
    lang = get_language()
    if lang.startswith('en'):
        lang = lang[:2]

    if not lang in conf.AVAIL_ASSET_LANG:
        lang = 'en'

    return conf.UPLOADCARE_JS % {'lang': lang}


class FileWidget(TextInput):
    input_type = 'hidden'

    class Media:
        js = (get_asset_lang(),)

    def __init__(self, attrs=None):
        default_attrs = {
            'role': 'uploadcare-line-uploader',
            'data-public-key': UploadCare().pub_key,
            'data-override-style': 'float: left;',
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
                fname = '<a href="%s">%s</a>' % (value.url, value.filename)
            else:
                fname = '%s (%s)' % (value.filename, _('unavail.'))

            description = '<p>%s: %s</p>' % (_('File'), fname)

            html = mark_safe(html + description)

        return html


class FileField(Field):
    widget = FileWidget
