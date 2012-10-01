#!/usr/bin/python
# encoding: utf-8

import argparse
import urlparse
import urllib
import logging
import pprint
import ConfigParser
import os.path

from pyuploadcare import UploadCare, UploadCareException


pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger('pyuploadcare')
settings = {
    'pub_key': None,
    'secret': None,
    'api_url': 'http://api.uploadcare.com/',
    'upload_url': 'http://upload.uploadcare.com/',
    'verify_api_ssl': True,
    'verify_upload_ssl': False,
    'api_version': '0.2',
    'custom_headers': None,
}


def create_ucare():
    return UploadCare(
        pub_key=settings['pub_key'],
        secret=settings['secret'],
        api_base=settings['api_url'],
        upload_base=settings['upload_url'],
        verify_api_ssl=settings['verify_api_ssl'],
        verify_upload_ssl=settings['verify_upload_ssl'],
        api_version=settings['api_version'],
        custom_headers=settings['custom_headers'],
    )


def list(args):
    ucare = create_ucare()
    query = {}
    for name in ['page', 'limit', 'kept', 'removed']:
        arg = getattr(args, name)
        if arg is not None:
            query[name] = arg
    q = urllib.urlencode(query)
    url = urlparse.urlunsplit(['', '', '/files/', q, ''])

    pp.pprint(ucare.make_request('GET', url))


def uc_file(url):
    ucare = create_ucare()
    return ucare.file(url)


def get(args):
    pp.pprint(uc_file(args.path).info)


def store(args):
    uc_file(args.path).store()


def delete(args):
    uc_file(args.path).delete()


def upload_from_url(args):
    ucare = create_ucare()
    ufile = ucare.file_from_url(args.url, wait=True)
    print 'token: {0.token}\nstatus: {0.status}'.format(ufile)


def upload(args):
    ucare = create_ucare()
    ufile = ucare.upload(args.filename)
    pp.pprint(ufile.info)


def get_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # list
    subparser = subparsers.add_parser('list', help='list all files')
    subparser.set_defaults(func=list)
    subparser.add_argument('--page', help='page to show')
    subparser.add_argument('--limit', help='files per page')
    subparser.add_argument('--kept', help='filter kept files',
                           choices=['all', 'true', 'false'])
    subparser.add_argument('--removed', help='filter removed files',
                           choices=['all', 'true', 'false'])

    # get
    subparser = subparsers.add_parser('get', help='get file info')
    subparser.set_defaults(func=get)
    subparser.add_argument('path', help='file path')

    # store
    subparser = subparsers.add_parser('store', help='store file')
    subparser.set_defaults(func=store)
    subparser.add_argument('path', help='file path')

    # delete
    subparser = subparsers.add_parser('delete', help='request delete')
    subparser.set_defaults(func=delete)
    subparser.add_argument('path', help='file path')

    # upload from url
    subparser = subparsers.add_parser('upload_from_url', help='upload file from url')
    subparser.set_defaults(func=upload_from_url)
    subparser.add_argument('url', help='file url')

    # upload
    subparser = subparsers.add_parser('upload', help='upload file')
    subparser.set_defaults(func=upload)
    subparser.add_argument('filename', help='filename')

    # common arguments
    parser.add_argument('--pub_key',
                        help='API key, if not set is read from uploadcare.ini'
                             ' and ~/.uploadcare config files')
    parser.add_argument('--secret',
                    help='API secret, if not set is read from uploadcare.ini'
                             ' and ~/.uploadcare config files')
    parser.add_argument('--api_url',
                        help='API url, can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.'
                             ' default: http://api.uploadcare.com/')
    parser.add_argument('--upload_url',
                        help='Upload API url, can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.'
                             ' default: http://upload.uploadcare.com/')
    parser.add_argument('--verify_upload_ssl',
                        action='store_true',
                        help='Verify ssl certificate of upload API url.'
                             ' Can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.')
    parser.add_argument('--verify_api_ssl',
                        action='store_true',
                        help='Verify ssl certificate of API url.'
                             ' Can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.')
    parser.add_argument('--api_version',
                    help='API version, can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.'
                             ' default: 0.2')
    parser.add_argument('-H', '--header',
                        help='Add custom HTTP headers, can be set several times.'
                             ' header_name:value.'
                             ' i.e. "ucare -H User-Agent:ie5 list"',
                        action='append')

    args = parser.parse_args()
    return args


def load_config_from_file(filename):
    filename = os.path.expanduser(filename)
    if not os.path.exists(filename):
        return

    config = ConfigParser.RawConfigParser()
    config.read(filename)

    for name in settings.keys():
        try:
            settings[name] = config.get('ucare', name)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            pass


def load_config_from_args(args):
    for name in settings.keys():
        arg = getattr(args, name, None)
        if arg is not None:
            settings[name] = arg
    custom_headers = {}
    if args.header is not None:
        for header in args.header:
            name, _, value = header.partition(':')
            custom_headers[name] = value
    settings['custom_headers'] = custom_headers

def main():
    args = get_args()
    load_config_from_file('~/.uploadcare')
    load_config_from_file('uploadcare.ini')
    load_config_from_args(args)

    try:
        args.func(args)
    except UploadCareException as e:
        print e


if __name__ == '__main__':
    main()
