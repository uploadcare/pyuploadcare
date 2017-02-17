# coding: utf-8
from __future__ import unicode_literals

from pyuploadcare import conf
import hashlib


def generate_secure_signature(secret=conf.secret, expire=conf.expire):
    """Generates secure signature for upload requests"""

    to_sign = str(secret) + str(int(expire))
    return hashlib.md5(to_sign).digest().encode('hex')
