# coding: utf-8
"""
Uploadcare REST client.

It is JSON REST request abstraction layer that is used by the
``pyuploadcare.api_resources``.

"""

from __future__ import unicode_literals
from platform import python_implementation, python_version
import email.utils
import hashlib
import hmac
import re
import logging
import json
import socket
import cgi
import time

import requests
import six

if six.PY3:
    from urllib.parse import urljoin, urlsplit
else:
    from urlparse import urljoin, urlsplit

from . import conf, __version__
from .exceptions import (
    APIConnectionError, AuthenticationError, APIError, InvalidRequestError,
    ThrottledRequestError,
)


logger = logging.getLogger("pyuploadcare")

# Use session for keep-alive connections.
session = requests.session()


def _get_timeout(timeout):
    if timeout is not conf.DEFAULT:
        return timeout
    if conf.timeout is not conf.DEFAULT:
        return conf.timeout
    return socket.getdefaulttimeout()


def _content_type_from_response(response):
    content_type = response.headers.get('Content-Type', '')
    content_type, _ = cgi.parse_header(content_type)
    return content_type


def _build_user_agent():
    extension_info = ''
    if conf.user_agent_extension:
        extension_info = '; {0}'.format(conf.user_agent_extension)
    return 'PyUploadcare/{0}/{1} ({2}/{3}{4})'.format(__version__,
                                                      conf.pub_key,
                                                      python_implementation(),
                                                      python_version(),
                                                      extension_info)


def rest_request(verb, path, data=None, timeout=conf.DEFAULT,
                 retry_throttled=conf.DEFAULT):
    """Makes REST API request and returns response as ``dict``.

    It provides auth headers as well and takes settings from ``conf`` module.

    Make sure that given ``path`` does not contain leading slash.

    Usage example::

        >>> rest_request('GET', 'files/?limit=10')
        {
            'next': 'https://api.uploadcare.com/files/?limit=10&page=2',
            'total': 1241,
            'page': 1,
            'pages': 125,
            'per_page': 10,
            'previous': None,
            'results': [
                # ...
                {
                    # ...
                    'uuid': 1921953c-5d94-4e47-ba36-c2e1dd165e1a,
                    # ...
                },
                # ...
            ]
        }

    """
    if retry_throttled is conf.DEFAULT:
        retry_throttled = conf.retry_throttled

    path = path.lstrip('/')
    url = urljoin(conf.api_base, path)
    url_parts = urlsplit(url)

    if url_parts.query:
        path = url_parts.path + '?' + url_parts.query
    else:
        path = url_parts.path

    content = ''
    if data is not None:
        content = json.dumps(data)

    content_type = 'application/json'
    content_md5 = hashlib.md5(content.encode('utf-8')).hexdigest()

    def _request():
        date = email.utils.formatdate(usegmt=True)
        sign_string = '\n'.join([
            verb,
            content_md5,
            content_type,
            date,
            path,
        ])
        sign_string_as_bytes = sign_string.encode('utf-8')

        try:
            secret_as_bytes = conf.secret.encode('utf-8')
        except AttributeError:
            secret_as_bytes = bytes()
        sign = hmac.new(secret_as_bytes, sign_string_as_bytes, hashlib.sha1) \
            .hexdigest()

        headers = {
            'Authorization': 'Uploadcare {0}:{1}'.format(conf.pub_key, sign),
            'Date': date,
            'Content-Type': content_type,
            'Accept': 'application/vnd.uploadcare-v{0}+json'.format(
                conf.api_version),
            'User-Agent': _build_user_agent(),
        }
        logger.debug('''sent:
            verb: {0}
            path: {1}
            headers: {2}
            data: {3}'''.format(verb, path, headers, content))

        try:
            response = session.request(verb, url, allow_redirects=True,
                                       verify=conf.verify_api_ssl,
                                       headers=headers, data=content,
                                       timeout=_get_timeout(timeout))
        except requests.RequestException as exc:
            raise APIConnectionError(exc.args[0])

        logger.debug(
            'got: {0} {1}'.format(response.status_code, response.text)
        )

        if 'warning' in response.headers:
            match = re.search('"(.+)"', response.headers['warning'])
            if match:
                for warning in match.group(1).split('; '):
                    logger.warn('API Warning: {0}'.format(warning))

        # No content.
        if response.status_code == 204:
            return {}
        if verb.lower() == 'options':
            return ''

        if 200 <= response.status_code < 300:
            if _content_type_from_response(response).endswith(('/json', '+json')):
                if verb.lower() == 'head':
                    return ''
                try:
                    return response.json()
                except ValueError as exc:
                    raise APIError(exc.args[0])

        if response.status_code in (401, 403):
            raise AuthenticationError(response.content)

        if response.status_code in (400, 404):
            raise InvalidRequestError(response.content)

        if response.status_code == 429:
            raise ThrottledRequestError(response)

        # Not json or unknown status code.
        raise APIError(response.content)

    while True:
        try:
            return _request()
        except ThrottledRequestError as e:
            if retry_throttled:
                logger.debug('Throttled, retry in {0} seconds'.format(e.wait))
                time.sleep(e.wait)
                retry_throttled -= 1
                continue
            else:
                raise


def uploading_request(verb, path, data=None, files=None, timeout=conf.DEFAULT):
    """Makes Uploading API request and returns response as ``dict``.

    It takes settings from ``conf`` module.

    Make sure that given ``path`` does not contain leading slash.

    Usage example::

        >>> file_obj = open('photo.jpg', 'rb')
        >>> uploading_request('POST', 'base/', files={'file': file_obj})
        {
            'file': '9b9f4483-77b8-40ae-a198-272ba6280004'
        }
        >>> File('9b9f4483-77b8-40ae-a198-272ba6280004')

    """
    path = path.lstrip('/')
    url = urljoin(conf.upload_base, path)

    if data is None:
        data = {}
    data['pub_key'] = conf.pub_key
    data['UPLOADCARE_PUB_KEY'] = conf.pub_key

    headers = {
        'User-Agent': _build_user_agent(),
    }

    try:
        response = session.request(
            str(verb), url, allow_redirects=True,
            verify=conf.verify_upload_ssl, data=data, files=files,
            headers=headers, timeout=_get_timeout(timeout),
        )
    except requests.RequestException as exc:
        raise APIConnectionError(exc.args[0])

    # No content.
    if response.status_code == 204:
        return {}

    if 200 <= response.status_code < 300:
        if _content_type_from_response(response).endswith(('/json', '+json')):
            try:
                return response.json()
            except ValueError as exc:
                raise APIError(exc.args[0])

    if response.status_code in (400, 404):
        raise InvalidRequestError(response.content)

    # Not json or unknown status code.
    raise APIError(response.content)
