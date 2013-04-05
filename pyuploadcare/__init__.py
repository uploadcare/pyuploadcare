__version__ = '0.18'

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
from pyuploadcare.exceptions import (
    UploadCareException, APIConnectionError, AuthenticationError,
    APIError, InvalidRequestError,
)


logger = logging.getLogger("pyuploadcare")
uuid_with_effects_regex = re.compile(ur'''
    (?P<uuid>[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12})
    (
        /-/(?P<effects>.*)
    )?
''', re.VERBOSE)


class UploadCare(UploaderMixin):
    def __init__(self, pub_key, secret, timeout=5,
                 api_base='https://api.uploadcare.com/',
                 upload_base='https://upload.uploadcare.com/',
                 cdn_base='https://ucarecdn.com/',
                 verify_api_ssl=True,
                 verify_upload_ssl=True,
                 custom_headers=None,
                 api_version='0.2',
                 **kwargs):
        self.pub_key = pub_key
        self.secret = secret
        self.timeout = timeout

        self.api_base = api_base
        self.upload_base = upload_base
        self.cdn_base = cdn_base

        self.verify_api_ssl = verify_api_ssl
        self.verify_upload_ssl = verify_upload_ssl
        self.custom_headers = custom_headers

        self._api_parts = urlparse.urlsplit(api_base)

        self.api_version = api_version
        self.accept = 'application/vnd.uploadcare-v{0}+json'.format(api_version)
        self.default_headers = {
            'User-Agent': 'pyuploadcare/{0}'.format(__version__),
        }

    def file(self, file_serialized):
        m = uuid_with_effects_regex.search(file_serialized)

        if not m:
            raise InvalidRequestError("Couldn't find UUID")

        f = File(file_id=m.groupdict()['uuid'], ucare=self,
                 default_effects=m.groupdict()['effects'])

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

        headers = self._build_headers({
            'Authorization': 'Uploadcare {0}:{1}'.format(self.pub_key, sign),
            'Date': date,
            'Content-Type': content_type,
            'Content-Length': str(len(content)),
            'Accept': self.accept,
        })
        logger.debug('''sent:
            verb: {0}
            path: {1}
            headers: {2}
            data: {3}'''.format(verb, path, headers, content))

        uri = self._build_api_uri(path)
        try:
            response = requests.request(verb, uri, allow_redirects=True,
                                        verify=self.verify_api_ssl,
                                        headers=headers, data=content)
        except requests.RequestException as exc:
            raise APIConnectionError(u'Network error: {exc}'.format(exc=exc))

        logger.debug('got: %s %s' % (response.status_code, response.content))

        if 'warning' in response.headers:
            match = re.search('"(.+)"', response.headers['warning'])
            if match:
                for warning in match.group(1).split('; '):
                    logger.warn('API Warning: {0}'.format(warning))

        # TODO: Add check for content-type.
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                raise APIError(u'API error: {exc}'.format(exc=exc))
        # No content.
        if response.status_code == 204:
            return

        if response.status_code == 403:
            raise AuthenticationError(
                u'Authentication error: {exc}'.format(exc=response.content)
            )

        if response.status_code in (400, 404):
            raise InvalidRequestError(
                u'Invalid request error: {exc}'.format(exc=response.content)
            )

        raise APIError(u'API error: {exc}'.format(exc=response.content))
