# coding: utf-8
from __future__ import unicode_literals
import os
import json


class MockResponse(object):
    def __init__(self, status, data=b'{}'):
        self.status_code = status
        self.content = data
        self.text = data.decode('utf-8')
        self.headers = {'Content-Type': 'application/vnd.uploadcare+json'}

    def json(self):
        """Returns the json-encoded content of a response, if any."""
        return json.loads(self.text)


class MockListResponse(MockResponse):
    def __init__(self):
        super(MockListResponse, self).__init__(
            200, b'{'
                 b'"results": [], "next": null, "previous": null,'
                 b'"total": 0, "per_page": 1'
                 b'}'
        )


def api_response_from_file(filename):
    path_to_tests_dir = os.path.dirname(__file__)
    path_to_file = os.path.join(path_to_tests_dir, 'api_responses', filename)

    with open(path_to_file, 'rb') as fp:
        return fp.read()
