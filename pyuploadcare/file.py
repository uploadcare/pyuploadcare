import time

class File(object):
    _info = None
    _cached_url = None

    def __init__(self, file_id, ucare):
        self.file_id = file_id
        self.ucare = ucare

    def __repr__(self):
        return '<uploadcare.File %s>' % self.file_id

    def keep(self, wait=False):
        self._info = self.ucare.make_request('POST', self.api_uri(), {'keep': 1})

        if wait:
            while not self.info['on_s3']:
                self.update_info()
                time.sleep(0.1)

    def delete(self):
        self.ucare.make_request('DELETE', self.api_uri())

    @property
    def info(self):
        if not self._info:
            self.update_info()

        return self._info

    def update_info(self):
        self._info = self.ucare.make_request('GET', self.api_uri())

    def api_uri(self):
        return '/files/%s/' % self.file_id

    def serialize(self):
        """Returns a string suitable to be stored somethere. It's either an URL (to save a request) or just file-id"""

        if self._info and self.url():
            return self.url()

        return self.file_id

    def url(self):
        if self._cached_url:
            return self._cached_url

        return self.info['original_file_url']

    def filename(self):
        return self.url().split('/')[-1]

