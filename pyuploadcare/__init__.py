# coding: utf-8
"""
PyUploadcare: a Python library for Uploadcare

Usage example::

    >>> import pyuploadcare
    >>> pyuploadcare.conf.pub_key = 'demopublickey'
    >>> pyuploadcare.conf.secret = 'demoprivatekey'
    >>> file_ = pyuploadcare.File('6c5e9526-b0fe-4739-8975-72e8d5ee6342')
    >>> file_.cdn_url
    https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/

"""

from __future__ import unicode_literals

__version__ = '1.0.1'

from .api_resources import File, FileGroup
from .exceptions import (
    UploadcareException, APIConnectionError, AuthenticationError, APIError,
    InvalidRequestError,
)
