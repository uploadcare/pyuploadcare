from django.forms import Field, HiddenInput, Media
from django.conf import settings

from pyuploadcare.dj import UploadCare

UPLOADCARE_JS = 'http://static.uploadcare.com/assets/uploaders/line-widget.en.js'

class FileWidget(HiddenInput):
    is_hidden = False

    class Media:
         js = (UPLOADCARE_JS,)
    
    def __init__(self, attrs=None):
        default_attrs = {'role': 'uploadcare-plain-uploader',
                         'data-public-key': UploadCare().pub_key}
        
        if attrs:
            default_attrs.update(attrs)
            
        super(FileWidget, self).__init__(default_attrs)
    

class FileField(Field):
    widget = FileWidget
