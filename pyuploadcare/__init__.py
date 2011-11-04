import httplib
import email.utils
import hashlib
import hmac
import urlparse
import re

try:
    import json
except ImportError:
    import simplejson as json

from .file import File

uuid_regex = re.compile(r'[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}')

class UploadCareException(Exception):
    def __init__(self, message, response=None):
        super(UploadCareException, self).__init__(message)
        self.response = response

    
class UploadCare(object):
    def __init__(self, pub_key, secret, timeout=5, api_base="http://api.uploadcare.com/"):
        self.pub_key = pub_key
        self.secret = secret
        self.timeout = timeout

        self.api_base = api_base

        parts = urlparse.urlsplit(api_base)

        self.host = parts.hostname
        self.port = parts.port
        self.path = parts.path

    def file(self, file_serialized):
        print 'serialized got: ', file_serialized
        m = uuid_regex.search(file_serialized)

        if not m:
            raise ValueError("Couldn't find UUID")

        f = File(m.group(0), self)

        if file_serialized.startswith('http'):
            f._cached_url = file_serialized
        
        return f



    def make_request(self, verb, uri, data=None):    
        parts = [''] + filter(None, self.path.split('/') + uri.split('/')) + ['']
        uri = '/'.join(parts)

        content = ''
    
        if data:
            content = json.dumps(data)
        
        content_type = 'application/json'
        content_md5 = hashlib.md5(content).hexdigest()
        date = email.utils.formatdate(usegmt=True)

        sign_string = '\n'.join([verb,
                                 content_md5,
                                 content_type,
                                 date,
                                 uri])

        sign = hmac.new(str(self.secret),
                        sign_string,
                        hashlib.sha1).hexdigest()
        
        headers = {
            'Authentication': 'UploadCare %s:%s' % (self.pub_key, sign),
            'Date': date,
            'Content-Type': content_type
            }

        con = httplib.HTTPConnection(self.host, self.port, timeout=self.timeout)
        con.request(verb, uri, content, headers)

#        assert False

        print 'sent: ', verb, uri, content

        response = con.getresponse()
        data = response.read()

        print 'got: ', response.status, data


        if response.status == 200: # Ok
            return json.loads(data)

        if response.status == 204: # No Content
            return

        raise UploadCareException('Response status is %i. Data: %s' % (response.status, data), response=response)




