# coding: utf-8
"""
PyUploadcare: a Python library for Uploadcare

"""

__version__ = '0.19'

from pyuploadcare.file import File, FileGroup
from pyuploadcare.exceptions import (
    UploadcareException, APIConnectionError, AuthenticationError, APIError,
    InvalidRequestError,
)
