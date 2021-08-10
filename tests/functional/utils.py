# coding: utf-8
from __future__ import unicode_literals

import json
import os

from requests import HTTPError


class MockResponse(object):
    def __init__(self, status, data=b'{}'):
        self.status_code = status
        self.content = data
        self.text = data.decode('utf-8')
        self.headers = {'Content-Type': 'application/vnd.uploadcare+json'}

    def json(self):
        """Returns the json-encoded content of a response, if any."""
        return json.loads(self.text)

    @classmethod
    def from_file(cls, filename, status=200):
        data = api_response_from_file(filename)
        return cls(status, data)

    def raise_for_status(self):
        if self.status_code != 200:
            raise HTTPError(self.status_code)


class MockListResponse(MockResponse):
    def __init__(self, status=200, data=None):
        template = (b'{'
                    b'"results": ' + (data or b'[]') + b', "next": null, '
                    b'"previous": null,'
                    b'"total": 0, "per_page": 1'
                    b'}')

        super(MockListResponse, self).__init__(status, template)


def api_response_from_file(filename):
    path_to_tests_dir = os.path.dirname(__file__)
    path_to_file = os.path.join(path_to_tests_dir, 'api_responses', filename)

    with open(path_to_file, 'rb') as fp:
        return fp.read()
