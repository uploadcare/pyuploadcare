# coding: utf-8
import json


class MockResponse(object):

    def __init__(self, status, data='{}'):
        self.status_code = status
        self.content = data
        self.headers = {}

    def json(self):
        """Returns the json-encoded content of a response, if any."""
        return json.loads(self.content)
