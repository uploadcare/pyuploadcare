from django.forms import Field, TextInput, Media
from django.conf import settings
from django.utils.safestring import mark_safe

UPLOADCARE_JS = 'http://static.uploadcare.com/assets/uploaders/line-widget.en.js'

class FileWidget(TextInput):
    input_type = 'hidden'

    class Media:
        js = (UPLOADCARE_JS,)
    
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
                fname = '%s (unavail.)' % value.filename()

            description = '<p>File: %s</p>' % fname

            html = mark_safe(html + description)

        return html
    

class FileField(Field):
    widget = FileWidget
