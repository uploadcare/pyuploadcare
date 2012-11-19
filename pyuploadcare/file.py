import time
import logging

import requests


logger = logging.getLogger("pyuploadcare")


# This function is helper for constuct similar proxy methods.
def make_cdn_command(method):
    def command(self, *args, **kwargs):
        return getattr(self.cdn_url, method)(*args, **kwargs)
    return command


class File(object):
    _info = None
    _cached_url = None

    def __init__(self, file_id, ucare):
        self.file_id = file_id
        self.ucare = ucare

    def __repr__(self):
        return '<uploadcare.File %s>' % self.file_id

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
        return CDNFile(self)

    @property
    def filename(self):
        if not self.url:
            return ''
        return self.url.split('/')[-1]

    # This method is just proxy to cdn_url methods.
    crop = make_cdn_command('crop')
    resize = make_cdn_command('resize')
    scale_crop = make_cdn_command('scale_crop')
    effect = make_cdn_command('effect')


class CDNFile(object):
    def __init__(self, file, command_string=''):
        self.file = file
        self.command_string = command_string

    def __str__(self):
        return '{base}{id}/{command}'.format(base=self.file.ucare.cdn_base,
            id=self.file.file_id, command=self.command_string)

    def _add_raw_command(self, command, args):
        """Return self copy with chainable applied command."""
        command_string = '-/{}/{}/'.format(command, args)
        return self.__class__(self.file, self.command_string + command_string)

    def crop(self, width, height, center=False, fill_color=None):
        args = ['{}x{}'.format(width, height)]
        if center:
            args.append('center')
        if fill_color is not None:
            # TODO: Does check needed? For example:
            # if len(fill_color) not in (3, 6):
            #     raise ValueError('Fill_color should be 3 or 6 hex digits.')
            # int(fill_color, 16)  # Will raise ValueError if not hex.
            args.append(fill_color)
        return self._add_raw_command('crop', '/'.join(args))

    def resize(self, width=None, height=None):
        if not width and not height:
            raise ValueError('Width or height reqired to resize.')

        dimensions = '{}x{}'.format(width or '', height or '')
        return self._add_raw_command('resize', dimensions)

    def scale_crop(self, width, height, center=False):
        args = ['{}x{}'.format(width, height)]
        if center:
            args.append('center')
        return self._add_raw_command('scale_crop', '/'.join(args))

    def effect(self, effect):
        return self._add_raw_command('effect', effect)
