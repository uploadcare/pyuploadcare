__version__ = (0, 8)

import email.utils
import hashlib
import hmac
import urlparse
import re
import logging
import json
import requests

from pyuploadcare.file import File
from pyuploadcare.uploader import UploaderMixin


logger = logging.getLogger("pyuploadcare")
uuid_regex = re.compile(r'[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}')


class UploadCareException(Exception):
    def __init__(self, response, data):
        message = 'Response status is %i. Data: %s' % (response.status_code, data)
        super(UploadCareException, self).__init__(message)
        self.response = response
        self.data = data


class UploadCare(UploaderMixin):
    def __init__(self, pub_key, secret, timeout=5,
                 api_base='http://api.uploadcare.com/',
                 upload_base='http://upload.uploadcare.com/',
                 verify_api_ssl=True,
                 verify_upload_ssl=True,
                 custom_headers=None,
                 api_version='0.2'):
        self.pub_key = pub_key
        self.secret = secret
        self.timeout = timeout

        self.api_base = api_base
        self.upload_base = upload_base

        self.verify_api_ssl = verify_api_ssl
        self.verify_upload_ssl = verify_upload_ssl
        self.custom_headers = custom_headers

        self._api_parts = urlparse.urlsplit(api_base)

        self.api_version = api_version
        if self.api_version == '0.1':
            self.accept = 'application/json'
        else:
            self.accept = 'application/vnd.uploadcare-v{}+json'.format(
                                api_version)
        self.default_headers = {
            'User-Agent': 'pyuploadcare/{}.{}'.format(*__version__),
        }

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

    def _build_api_path(self, path):
        """Abomination"""
        uri_parts = urlparse.urlsplit(path)
        parts = filter(None, self._api_parts.path.split('/') + uri_parts.path.split('/'))
        path = '/'.join([''] + parts + [''])
        api_path = urlparse.urlunsplit(['', '', path, uri_parts.query, ''])
        return api_path

    def _build_api_uri(self, path):
        """Abomination"""
        base = urlparse.urlunsplit([
            self._api_parts.scheme,
            self._api_parts.netloc,
            '', '', ''
        ])
        return base + path

    def _build_headers(self, headers=None):
        result = dict(self.default_headers)
        if headers is not None:
            result.update(headers)
        if self.custom_headers is not None:
            result.update(self.custom_headers)
        return result

    def make_request(self, verb, path, data=None):

        path = self._build_api_path(path)
        content = ''

        if data is not None:
            content = json.dumps(data)

        content_type = 'application/json'
        content_md5 = hashlib.md5(content).hexdigest()
        date = email.utils.formatdate(usegmt=True)

        sign_string = '\n'.join([
            verb,
            content_md5,
            content_type,
            date,
            path,
        ])

        sign = hmac.new(str(self.secret),
                        sign_string,
                        hashlib.sha1).hexdigest()


        # TODO: remove this when bugs are fixed and api is deployed to production
        if self.api_version == '0.1':
            auth_header_name = 'Authentication'
        else:
            auth_header_name = 'Authorization'

        headers = self._build_headers({
            auth_header_name: 'UploadCare {}:{}'.format(self.pub_key, sign),
            'Date': date,
            'Content-Type': content_type,
            'Content-Length': str(len(content)),
            'Accept': self.accept,
        })
        logger.debug('''sent:
            verb: {}
            path: {}
            headers: {}
            data: {}'''.format(verb, path, headers, content))

        uri = self._build_api_uri(path)
        response = requests.request(verb, uri, allow_redirects=True,
                                    verify=self.verify_api_ssl,
                                    headers=headers, data=content)

        logger.debug('got: %s %s' % (response.status_code, response.content))

        if 'warning' in response.headers:
            match = re.search('"(.+)"', response.headers['warning'])
            if match:
                for warning in match.group(1).split('; '):
                    logger.warn('API Warning: {}'.format(warning))

        if response.status_code == 200: # Ok
            if response.json is None:
                raise ValueError('no json in response')
            return response.json

        if response.status_code == 204: # No Content
            return

        raise UploadCareException(response, response.content)
