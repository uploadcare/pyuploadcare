# coding: utf-8
import time
import logging

import requests
from pyuploadcare.exceptions import TimeoutError, InvalidRequestError


logger = logging.getLogger("pyuploadcare")


class File(object):
    _info = None
    _cached_url = None

    def __init__(self, file_id, ucare, default_effects=''):
        self.file_id = file_id
        self.ucare = ucare
        self.default_effects = default_effects

    def __repr__(self):
        return '<uploadcare.File %s>' % self.file_id

    def __str__(self):
        return self.cdn_url

    def __getattr__(self, name):
        if name.startswith('resized_') or name.startswith('cropped_'):
            width, _, height = name[8:].partition('x')
            try:
                width = int(width) if width else None
            except ValueError as exc:
                raise InvalidRequestError(
                    u'invalid width, {exc}'.format(exc=exc)
                )
            try:
                height = int(height) if height else None
            except ValueError as exc:
                raise InvalidRequestError(
                    u'invalid height, {exc}'.format(exc=exc)
                )
            func = self.cropped if name.startswith('c') else self.resized
            return func(width, height)

        return super(File, self).__getattr__(name)

    def keep(self, **kwargs):
        """Deprecated method.

        Use store instead.
        Will be removed eventually.
        """
        logger.warn("keep() is deprecated, use store() instead")
        return self.store(**kwargs)

    def store(self, wait=False, timeout=5):
        self.ucare.make_request('PUT', self.storage_uri)

        if wait:
            time_started = time.time()
            while not (self.is_on_s3 and self.is_stored):
                if time.time() - time_started > timeout:
                    raise TimeoutError('timed out trying to store')
                self.update_info()
                time.sleep(0.1)
            self.ensure_on_cdn()
        self.update_info()

    def delete(self, wait=False, timeout=5):
        self.ucare.make_request('DELETE', self.api_uri)

        if wait:
            time_started = time.time()
            while not self.is_removed:
                if time.time() - time_started > timeout:
                    raise TimeoutError('timed out trying to delete')
                self.update_info()
                time.sleep(0.1)
        self.update_info()

    def ensure_on_s3(self, timeout=5):
        time_started = time.time()
        while not self.is_on_s3:
            if time.time() - time_started > timeout:
                raise TimeoutError('timed out waiting for uploading to s3')
            self.update_info()
            time.sleep(0.1)

    def ensure_on_cdn(self, timeout=5):
        if not self.is_on_s3:
            raise InvalidRequestError('file is not on s3 yet')
        if not self.is_stored:
            raise InvalidRequestError('file is private')
        time_started = time.time()
        while True:
            if time.time() - time_started > timeout:
                raise TimeoutError('timed out waiting for file appear on cdn')
            resp = requests.head(self.cdn_url, headers=self.ucare.default_headers)
            if resp.status_code == 200:
                return
            logger.debug(resp)
            time.sleep(0.1)

    @property
    def info(self):
        if not self._info:
            self.update_info()
        return self._info

    def update_info(self):
        self._info = self.ucare.make_request('GET', self.api_uri)

    @property
    def is_on_s3(self):
        return self.info['on_s3']

    @property
    def is_stored(self):
        return self.info['last_keep_claim'] is not None

    @property
    def is_removed(self):
        return self.info['removed'] is not None

    @property
    def api_uri(self):
        return '/files/{0}/'.format(self.file_id)

    @property
    def storage_uri(self):
        return '/files/{0}/storage/'.format(self.file_id)

    def serialize(self):
        """Returns a string suitable to be stored somewhere.

        It's either an URL (to save a request) or just file-id.

        """
        if self._info and self.url:
            return self.url

        return self.file_id

    @property
    def url(self):
        if self._cached_url:
            return self._cached_url
        return self.info['original_file_url']

    @property
    def cdn_url(self):
        if self.default_effects:
            return '{cdn_base}{uuid}/-/{effects}'.format(
                cdn_base=self.ucare.cdn_base,
                uuid=self.file_id,
                effects=self.default_effects
            )
        else:
            return '{cdn_base}{uuid}/'.format(
                cdn_base=self.ucare.cdn_base,
                uuid=self.file_id
            )

    @property
    def filename(self):
        if not self.url:
            return ''
        return self.url.split('/')[-1]

    def cropped(self, width=None, height=None):
        logger.warn("cropped() is deprecated, use cdn_url with "
                    "concatenated process command string")
        if not width or not height:
            raise InvalidRequestError('Need both width and height to crop')
        dimensions = '{0}x{1}'.format(width, height)

        return '{0}-/crop/{1}/'.format(self.cdn_url, dimensions)

    def resized(self, width=None, height=None):
        logger.warn("resized() is deprecated, use cdn_url with "
                    "concatenated process command string")
        if not width and not height:
            raise InvalidRequestError('Need width or height to resize')
        dimensions = str(width) if width else ''
        if height:
            dimensions += 'x{0}'.format(height)

        return '{0}-/resize/{1}/'.format(self.cdn_url, dimensions)
