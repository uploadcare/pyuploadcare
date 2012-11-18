
from django.template import Library

from pyuploadcare.file import File, CDNFile


register = Library()


# Helper for constuct template filters.
def make_cdn_file_filter(command):
    @register.filter(command)
    def cdn_filter(obj, params=None):
        if isinstance(obj, File):
            return obj.cdn_url._add_raw_command(command, params)
        if isinstance(obj, CDNFile):
            return obj._add_raw_command(command, params)
        return obj
    return cdn_filter


make_cdn_file_filter('crop')
make_cdn_file_filter('resize')
make_cdn_file_filter('scale_crop')
make_cdn_file_filter('effect')
