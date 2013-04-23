# coding: utf-8
"""
Uploadcare REST client.

It is JSON REST request abstraction layer that is used by the
``pyuploadcare.api_resources``.

"""

import email.utils
import hashlib
import hmac
import urlparse
import re
import logging
import json

import requests

from . import conf, __version__
from .exceptions import (
    APIConnectionError, AuthenticationError, APIError, InvalidRequestError,
)


logger = logging.getLogger("pyuploadcare")


def _build_api_path(api_base, path):
    uri_parts = urlparse.urlsplit(path)
    api_parts = urlparse.urlsplit(api_base)
    parts = filter(None, api_parts.path.split('/') + uri_parts.path.split('/'))
    path = '/'.join([''] + parts + [''])
    api_path = urlparse.urlunsplit(['', '', path, uri_parts.query, ''])
    return api_path


def _build_api_uri(api_base, path):
    api_parts = urlparse.urlsplit(api_base)
    base = urlparse.urlunsplit([
        api_parts.scheme,
        api_parts.netloc,
        '', '', ''
    ])
    return base + path


class RESTClient(object):

    @classmethod
    def make_request(cls, verb, path, data=None):
        path = _build_api_path(conf.api_base, path)
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

        sign = hmac.new(str(conf.secret), sign_string, hashlib.sha1) \
            .hexdigest()

        headers = {
            'Authorization': 'Uploadcare {0}:{1}'.format(conf.pub_key, sign),
            'Date': date,
            'Content-Type': content_type,
            'Content-Length': str(len(content)),
            'Accept': 'application/vnd.uploadcare-v{0}+json'.format(conf.api_version),
            'User-Agent': 'pyuploadcare/{0}'.format(__version__),
        }
        logger.debug('''sent:
            verb: {0}
            path: {1}
            headers: {2}
            data: {3}'''.format(verb, path, headers, content))

        uri = _build_api_uri(conf.api_base, path)
        try:
            response = requests.request(verb, uri, allow_redirects=True,
                                        verify=conf.verify_api_ssl,
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


class UploadingClient(object):

    @classmethod
    def make_request(cls, verb, path, data=None, files=None):
        path = _build_api_path(conf.upload_base, path)
        uri = _build_api_uri(conf.upload_base, path)

        if data is None:
            data = {}
        data['pub_key'] = conf.pub_key
        data['UPLOADCARE_PUB_KEY'] = conf.pub_key

        try:
            response = requests.request(
                verb, uri, allow_redirects=True, verify=conf.verify_upload_ssl,
                data=data, files=files
            )
        except requests.RequestException as exc:
            raise APIConnectionError(u'Network error: {exc}'.format(exc=exc))

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                raise APIError(u'API error: {exc}'.format(exc=exc))

        if response.status_code in (400, 404):
            raise InvalidRequestError(
                u'Invalid request error: {exc}'.format(exc=response.content)
            )

        raise APIError(u'API error: {exc}'.format(exc=response.content))
