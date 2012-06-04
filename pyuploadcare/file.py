import time
import logging

logger = logging.getLogger("pyuploadcare")


RESIZER_BASE = 'http://services.uploadcare.com/resizer/%(file_id)s/%(cmd_line)s/'


class LazyFile(object):
    def __init__(self, id, ucare):
        self.id = id
        self.ucare = ucare

    def load_data(self):
        return self.ucare.make_request('GET', '/files/download/%s/' % self.id)

    def wait(self):
        while True:
            data = self.load_data()
            logger.debug('loaded data %s' % data)

            if data['status'] == 'success':
                return File(data['file_id'], self.ucare)

            if data['status'] not in ('progress', 'unknown'):
                raise Exception('Invalid task status')

            time.sleep(0.1)


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

    def keep(self, wait=False):
        self._info = self.ucare.make_request('POST', self.api_uri, {'keep': 1})

        if wait:
            while not self.info['on_s3']:
                self.update_info()
                time.sleep(0.1)

    def delete(self):
        self.ucare.make_request('DELETE', self.api_uri)

    @property
    def info(self):
        if not self._info:
            self.update_info()

        return self._info

    def update_info(self):
        self._info = self.ucare.make_request('GET', self.api_uri)

    @property
    def api_uri(self):
        return '/files/%s/' % self.file_id

    def serialize(self):
        """Returns a string suitable to be stored somewhere.
        It's either an URL (to save a request) or just file-id"""

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

        return RESIZER_BASE % {'file_id': self.file_id, 'cmd_line': cmd_line}

    def string_resized(self, cmd_line):
        cmd_line = cmd_line.replace('_', '/')

        return RESIZER_BASE % {'file_id': self.file_id, 'cmd_line': cmd_line}
