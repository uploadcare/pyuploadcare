import json
import time

import requests

from pyuploadcare.file import File


class UploaderException(Exception):
    pass


class UploadedFile(object):
    def __init__(self, uploader, url, token):
        self.uploader = uploader
        self.url = url
        self.token = token
        self.status = None
        self.data = None

    def __repr__(self):
        return '<uploadcare.UploadedFile {} {}>'.format(self.url, self.status)

    def update_status(self):
        self.status, self.data = self.uploader.get_status(self.token)

    def wait(self, timeout=30):
        """Wait for upload to complete for `timeout` seconds"""
        time_started = time.time()
        while True:
            if time.time() - time_started > timeout:
                return False
            self.update_status()
            if self.status in ('success', 'failed'):
                return True
            time.sleep(0.1)

    def get_file(self):
        """Get uploadcare.file.File

        Return File instance if upload is complete, else None.

        """
        if self.status == 'success' and 'file_id' in self.data:
            return File(self.data['file_id'], self.uploader)
        return None


class UploaderMixin(object):
    def upload_from_url(self, url, wait=False, timeout=30):
        """Upload file from given URL

        Return UploadedFile instance.
        If `wait` is True, wait for upload to complete for `timeout` seconds.

        """
        url_from = '{}from_url/'.format(self.upload_base)
        response = requests.get(
            url_from,
            params={
                'source_url': url,
                'pub_key': self.pub_key,},
            verify=self.verify_upload_ssl,
            headers=self._build_headers(),
        )
        if response.status_code != 200:
            raise UploaderException(
                'status code: {}'.format(response.status_code))
        data = json.loads(response.content)
        if 'token' not in data:
            raise UploaderException(
                'could not find token in response: {}'.format(data))
        token = data['token']
        _file = UploadedFile(self, url, token)
        if wait:
            _file.wait(timeout=timeout)
        return _file

    def get_status(self, token):
        url_status = '{}from_url/status/'.format(self.upload_base)
        response = requests.get(
            url_status,
            params={'token': token},
            verify=self.verify_upload_ssl,
            headers=self._build_headers(),
        )

        if response.status_code != 200:
            raise UploaderException(
                'status code: {}'.format(response.status_code))
        data = json.loads(response.content)
        if 'status' not in data:
            raise UploaderException(
                'could not find status in response: {}'.format(data))

        return data['status'], data

    def upload(self, filename):
        with open(filename) as f:
            response = requests.post(
                '{}base/'.format(self.upload_base),
                data={'UPLOADCARE_PUB_KEY': self.pub_key},
                files={'file': f},
                verify=self.verify_upload_ssl,
                headers=self._build_headers(),
            )
            if response.status_code == 200:
                data = json.loads(response.content)
                return self.file(data['file'])
            raise UploaderException(
                'status code: {}'.format(response.status_code))
