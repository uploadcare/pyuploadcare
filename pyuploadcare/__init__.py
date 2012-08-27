__version__ = (0, 7)

import httplib
import email.utils
import hashlib
import hmac
import urlparse
import re
import logging
import json

from pyuploadcare.file import File
from pyuploadcare.uploader import UploaderMixin


logger = logging.getLogger("pyuploadcare")
uuid_regex = re.compile(r'[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}')


class UploadCareException(Exception):
    def __init__(self, response, data):
        message = 'Response status is %i. Data: %s' % (response.status, data)
        super(UploadCareException, self).__init__(message)
        self.response = response
        self.data = data


class UploadCare(UploaderMixin):
    def __init__(self, pub_key, secret, timeout=5,
                 api_base='http://api.uploadcare.com/',
                 upload_base='http://upload.uploadcare.com/',
                 api_version='0.2'):
        self.pub_key = pub_key
        self.secret = secret
        self.timeout = timeout

        self.api_base = api_base
        self.upload_base = upload_base

        parts = urlparse.urlsplit(api_base)

        self.secure = parts.scheme == 'https'
        self.host = parts.hostname
        self.port = parts.port
        self.path = parts.path

        self.api_version = api_version
        if self.api_version == '0.1':
            self.accept = 'application/json'
        else:
            self.accept = 'application/vnd.uploadcare-v{}+json'.format(
                                api_version)
        self.user_agent = 'pyuploadcare/{}.{}'.format(*__version__)

    def file(self, file_serialized):
        m = uuid_regex.search(file_serialized)

        if not m:
            raise ValueError("Couldn't find UUID")

        f = File(m.group(0), self)

        if file_serialized.startswith('http'):
            f._cached_url = file_serialized

        return f

    def file_from_url(self, url, wait=False, timeout=30):
        return self.upload_from_url(url, wait, timeout)

    def _build_uri(self, uri):
        """Abomination"""
        uri_parts = urlparse.urlsplit(uri)
        parts = filter(None, self.path.split('/') + uri_parts.path.split('/'))
        path = '/'.join([''] + parts + [''])
        uri = urlparse.urlunsplit(['', '', path, uri_parts.query, ''])
        return uri

    def make_request(self, verb, uri, data=None, extra_headers=None):
        uri = self._build_uri(uri)
        content = ''

        if data:
            content = json.dumps(data)

        content_type = 'application/json'
        content_md5 = hashlib.md5(content).hexdigest()
        date = email.utils.formatdate(usegmt=True)

        sign_string = '\n'.join([
            verb,
            content_md5,
            content_type,
            date,
            uri,
        ])

        sign = hmac.new(str(self.secret),
                        sign_string,
                        hashlib.sha1).hexdigest()

        headers = {
            'Authentication': 'UploadCare %s:%s' % (self.pub_key, sign),
            'Date': date,
            'Content-Type': content_type,
            'Accept': self.accept,
            'User-Agent': self.user_agent,
        }
        if extra_headers is not None:
            headers.update(extra_headers)

        if self.secure:
            con_class = httplib.HTTPSConnection
        else:
            con_class = httplib.HTTPConnection

        con = con_class(self.host, self.port, timeout=self.timeout)
        con.request(verb, uri, content, headers)

        logger.debug('sent: %s %s %s' % (verb, uri, content))

        response = con.getresponse()
        data = response.read()
        # head = response.getheaders()

        logger.debug('got: %s %s' % (response.status, data))

        if response.status == 200: # Ok
            return json.loads(data)

        if response.status == 204: # No Content
            return

        raise UploadCareException(response, data)
