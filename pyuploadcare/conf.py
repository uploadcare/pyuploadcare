# coding: utf-8
"""
Configuration variables.

"""

from __future__ import unicode_literals

# Do not import vars from this module.
# Instead import whole module and work with attributes.
__all__ = []

DEFAULT = object()

pub_key = None
secret = None

api_version = '0.5'
api_base = 'https://api.uploadcare.com/'
upload_base = 'https://upload.uploadcare.com/'
cdn_base = 'https://ucarecdn.com/'

verify_api_ssl = True
verify_upload_ssl = True

timeout = DEFAULT

# retry throttled requests this many times
retry_throttled = 1

user_agent_extension = None
