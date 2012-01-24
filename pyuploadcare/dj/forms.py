from django.forms import Field, TextInput, Media
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, get_language
from pyuploadcare.dj.conf import USE_HOSTED_ASSETS

UPLOADCARE_JS = 'http://static.uploadcare.com/assets/uploaders/line-widget.%(lang)s.js'
UPLOADCARE_LOCAL_JS = 'uploadcare/assets/uploaders/line-widget.%(lang)s.js'

AVAIL_ASSET_LANG = ('en', 'ru', 'pl')

def get_asset_lang():
    '''returns a localized asset url '''
    lang = get_language()
    if lang.startswith('en'):
        lang = lang[:2]

    if not lang in AVAIL_ASSET_LANG:
        lang = 'en'

    BASE_ASSET_URL = UPLOADCARE_JS
    if not USE_HOSTED_ASSETS:
        BASE_ASSET_URL = UPLOADCARE_LOCAL_JS

    return BASE_ASSET_URL % {'lang' : lang}


class FileWidget(TextInput):
    input_type = 'hidden'

    class Media:
        js = (get_asset_lang(),)
    

    def __init__(self, attrs=None):
        from pyuploadcare.dj import UploadCare

        default_attrs = {'role': 'uploadcare-line-uploader',
                         'data-public-key': UploadCare().pub_key,
                         'data-override-style': 'float: left;'}
        
        if attrs:
            default_attrs.update(attrs)
            
        super(FileWidget, self).__init__(default_attrs)

    def render(self, name, value, attrs):
        html = super(FileWidget, self).render(name, value, attrs)

        if value:
            if value.url():
                fname = '<a href="%s">%s</a>' % (value.url(), value.filename())
            else:
                fname = '%s (%s)' % (value.filename(), _('unavail.'))

            description = '<p>%s: %s</p>' % (_('File'), fname)

            html = mark_safe(html + description)

        return html
    

class FileField(Field):
    widget = FileWidget
