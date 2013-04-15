# coding: utf-8
"""
PyUploadcare: a Python library for Uploadcare

"""

__version__ = '0.19'

from pyuploadcare.api_requestor import UploadCare
from pyuploadcare.file import File, FileGroup
from pyuploadcare.exceptions import (
    UploadCareException, APIConnectionError, AuthenticationError, APIError,
    InvalidRequestError,
)
