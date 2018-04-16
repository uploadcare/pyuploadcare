# coding: utf-8
from __future__ import unicode_literals

from django import get_version as django_version
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .. import conf
from .. import __version__ as library_version


if not hasattr(settings, 'UPLOADCARE'):
    raise ImproperlyConfigured('UPLOADCARE setting must be set')

if 'pub_key' not in settings.UPLOADCARE:
    raise ImproperlyConfigured('UPLOADCARE setting must have pub_key')
if 'secret' not in settings.UPLOADCARE:
    raise ImproperlyConfigured('UPLOADCARE setting must have secret')


conf.pub_key = settings.UPLOADCARE['pub_key']
conf.secret = settings.UPLOADCARE['secret']
conf.user_agent_extension = 'Django/{0}; PyUploadcare-Django/{1}'.format(
    django_version(), library_version)

if 'cdn_base' in settings.UPLOADCARE:
    conf.cdn_base = settings.UPLOADCARE['cdn_base']


widget_version = settings.UPLOADCARE.get('widget_version', '3.x')
widget_build = settings.UPLOADCARE.get(
    'widget_build',
    settings.UPLOADCARE.get('widget_variant', 'full.min'))

widget_filename = 'uploadcare.{0}.js'.format(widget_build).replace('..', '.')

hosted_url = (
    'https://ucarecdn.com/libs/widget/{version}/{filename}'
    .format(version=widget_version, filename=widget_filename))

local_url = 'uploadcare/{filename}'.format(filename=widget_filename)

use_hosted_assets = settings.UPLOADCARE.get('use_hosted_assets', True)

if use_hosted_assets:
    uploadcare_js = hosted_url
else:
    uploadcare_js = settings.UPLOADCARE.get('widget_url', local_url)

upload_base_url = settings.UPLOADCARE.get('upload_base_url')
