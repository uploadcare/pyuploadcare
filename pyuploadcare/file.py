import time
import logging

logger = logging.getLogger("pyuploadcare")


RESIZER_BASE = 'http://services.uploadcare.com/resizer/{file_id}/{cmd_line}/'


class File(object):
    _info = None
    _cached_url = None

    def __init__(self, file_id, ucare):
        self.file_id = file_id
        self.ucare = ucare

    def __repr__(self):
        return '<uploadcare.File %s>' % self.file_id

    def __getattr__(self, name):
        if name.startswith('resized_'):
            return self.string_resized(name[8:])

        return super(File, self).__getattr__(name)

    def keep(self, **kwargs):
        """Deprecated method.

        Use store instead.
        Will be removed eventually.
        """
        logger.warn("keep() is deprecated, use store() instead")
        return self.store(**kwargs)

    def store(self, wait=False, timeout=5):
        if self.ucare.api_version == '0.1':
            self._info = self.ucare.make_request('POST', self.api_uri, data={
                'keep': 1
            })
        else:
            self.ucare.make_request('PUT', self.storage_uri)

        if wait:
            time_started = time.time()
            while not self.info['on_s3']:
                if time.time() - time_started > timeout:
                    raise Exception('timed out trying to store')
                self.update_info()
                time.sleep(0.1)
        self.update_info()

    def delete(self, wait=False, timeout=5):
        self.ucare.make_request('DELETE', self.api_uri)

        if wait:
            time_started = time.time()
            while self.info['removed'] is None:
                if time.time() - time_started > timeout:
                    raise Exception('timed out trying to delete')
                self.update_info()
                time.sleep(0.1)
        self.update_info()

    @property
    def info(self):
        if not self._info:
            self.update_info()
        return self._info

    def update_info(self):
        self._info = self.ucare.make_request('GET', self.api_uri)

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
    def filename(self):
        if not self.url:
            return ''
        return self.url.split('/')[-1]

    def resized(self, width=None, height=None, crop=False):
        dimensions = str(width or '')
        if height:
            dimensions += 'x%i' % height

        chunks = [dimensions]
        if crop:
            chunks.append('crop')

        cmd_line = '/'.join(chunks)
        return RESIZER_BASE.format(file_id=self.file_id, cmd_line=cmd_line)

    def string_resized(self, cmd_line):
        cmd_line = cmd_line.replace('_', '/')
        return RESIZER_BASE.format(file_id=self.file_id, cmd_line=cmd_line)
