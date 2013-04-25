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


def rest_request(verb, path, data=None):
    assert not path.startswith('/'), path
    url = urlparse.urljoin(conf.api_base, path)
    url_parts = urlparse.urlsplit(url)
    path = '{path}?{query}'.format(path=url_parts.path, query=url_parts.query)

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

    try:
        response = requests.request(verb, url, allow_redirects=True,
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


def uploading_request(verb, path, data=None, files=None):
    assert not path.startswith('/'), path
    url = urlparse.urljoin(conf.upload_base, path)

    if data is None:
        data = {}
    data['pub_key'] = conf.pub_key
    data['UPLOADCARE_PUB_KEY'] = conf.pub_key

    try:
        response = requests.request(
            verb, url, allow_redirects=True, verify=conf.verify_upload_ssl,
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
