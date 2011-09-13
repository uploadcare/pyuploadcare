
class File(object):
    _info = None
    _cached_url = None

    def __init__(self, file_id, ucare):
        self.file_id = file_id
        self.ucare = ucare

    def __repr__(self):
        return '<uploadcare.File %s>' % self.file_id

    def keep(self):
        self._info = self.ucare.make_request('POST', self.api_uri(), {'keep': 1})

    @property
    def info(self):
        if not self._info:
            self.update_info()

        return self._info

    def update_info(self):
        self._info = self.ucare.make_request('GET', self.api_uri())

    def url(self):
        if self._cached_url:
            return self._cached_url

        return self.info['original_file_url']

    def api_uri(self):
        return '/files/%s/' % self.file_id

    def serialize(self):
        """Returns a string suitable to be stored somethere. It's either an URL (to save a request) or just file-id"""

        if self._info and self.url():
            return self.url()

        return self.file_id