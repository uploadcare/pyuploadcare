import httplib
import email.utils
import hashlib
import hmac

from django.utils import simplejson as json

UPLOADCARE_PUB_KEY = 'kfahdkfahfskagufdlfuga'
UPLOADCARE_SECRET = 'd89syw4i8gofwdf8wye393dw'


def make_request(verb, uri, data=None):    
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

    print sign_string

    sign = hmac.new(str(UPLOADCARE_SECRET),
                    sign_string,
                    hashlib.sha1).hexdigest()
    
    headers = {
        'Authentication': 'UploadCare %s:%s' % (UPLOADCARE_PUB_KEY, sign),
        'Date': date,
        'Content-Type': content_type
        }

    con = httplib.HTTPConnection('0.0.0.0', 8000, timeout=1)
    con.set_debuglevel(1)

    resp = con.request(verb, uri, content, headers)
    
    return json.load(con.getresponse())

    

def tests():
    print make_request('GET', '/api/files/FILECARE_6/')
    print make_request('POST', '/api/files/FILECARE_5/', {'keep': 0})
    print make_request('GET', '/api/files/')


def keep(file_id):
    """Tells UploadCare to keep the file"""
    return make_request('POST', '/api/files/%s/' % file_id, {'keep': 1})



if __name__ == '__main__':
    tests()
