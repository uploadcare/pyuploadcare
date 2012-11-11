import time
import logging

import requests


logger = logging.getLogger("pyuploadcare")


class File(object):
    _info = None
    _cached_url = None

    def __init__(self, file_id, ucare):
        self.file_id = file_id
        self.ucare = ucare

    def __repr__(self):
        return '<uploadcare.File %s>' % self.file_id

    def __getattribute__(self, name):
        if name.startswith('resized_') or name.startswith('cropped_'):
            width, _, height = name[8:].partition('x')
            width = int(width) if width else None
            height = int(height) if height else None
            func = self.cropped if name.startswith('c') else self.resized
            return func(width, height)

        return super(File, self).__getattribute__(name)

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
                    raise Exception('timed out trying to store')
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
                    raise Exception('timed out trying to delete')
                self.update_info()
                time.sleep(0.1)
        self.update_info()

    def ensure_on_s3(self, timeout=5):
        time_started = time.time()
        while not self.is_on_s3:
            if time.time() - time_started > timeout:
                raise Exception('timed out waiting for uploading to s3')
            self.update_info()
            time.sleep(0.1)

    def ensure_on_cdn(self, timeout=5):
        if not self.is_on_s3:
            raise Exception('file is not on s3 yet')
        if not self.is_stored:
            raise Exception('file is private')
        time_started = time.time()
        while True:
            if time.time() - time_started > timeout:
                raise Exception('timed out waiting for file appear on cdn')
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
        return '/files/{}/'.format(self.file_id)

    @property
    def storage_uri(self):
        return '/files/{}/storage/'.format(self.file_id)

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
        if self.is_on_s3 and self.is_stored:
            fmt = self.ucare.cdn_base + '{uuid}/'
            return fmt.format(uuid=self.file_id)
        raise Exception('No CDN url for private file')

    @property
    def filename(self):
        if not self.url:
            return ''
        return self.url.split('/')[-1]

    def cropped(self, width=None, height=None):
        logger.warn("cropped() is deprecated, use cdn_url with "
                    "concatenated process command string")
        if not width or not height:
            raise ValueError('Need both width and height to crop')
        dimensions = '{}x{}'.format(width, height)

        return '{}-/crop/{}/'.format(self.cdn_url, dimensions)

    def resized(self, width=None, height=None):
        logger.warn("resized() is deprecated, use cdn_url with "
                    "concatenated process command string")
        if not width and not height:
            raise ValueError('Need width or height to resize')
        dimensions = str(width) if width else ''
        if height:
            dimensions += 'x{}'.format(height)

        return '{}-/resize/{}/'.format(self.cdn_url, dimensions)
