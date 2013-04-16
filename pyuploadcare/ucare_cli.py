#!/usr/bin/python
# encoding: utf-8

import argparse
import urlparse
import urllib
import logging
import pprint
import ConfigParser
import os.path

from pyuploadcare import UploadCare, UploadCareException, __version__


pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger('pyuploadcare')
settings = {
    'pub_key': None,
    'secret': None,
    'api_url': 'https://api.uploadcare.com/',
    'upload_url': 'https://upload.uploadcare.com/',
    'verify_api_ssl': True,
    'verify_upload_ssl': True,
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


def list_files(args=None):
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


def get_file(args):
    pp.pprint(uc_file(args.path).info)


def store_file(args):
    uc_file(args.path).store(wait=args.wait)


def delete_file(args):
    uc_file(args.path).delete(wait=args.wait)


def _check_upload_args(args):
    if not args.secret and (args.store or args.info):
        print 'Cannot store or get info without "--secret" key'
        return False
    return True


def _handle_uploaded_file(uf, args):
    if args.store:
        uf.store(wait=True)
        print 'File stored successfully.'

    if args.info:
        pp.pprint(uf.info)

    if args.cdnurl:
        print 'CDN url: {0}'.format(uf.cdn_url)


def upload_from_url(args):
    if not _check_upload_args(args):
        return
    ucare = create_ucare()
    ufile = ucare.file_from_url(args.url, wait=(args.wait or args.store))
    print 'token: {0.token}\nstatus: {0.status}'.format(ufile)

    if args.store or args.info:
        _file = ufile.get_file()
        if _file is None:
            print 'Cannot store or get info.'
            return

        _handle_uploaded_file(_file, args)


def upload(args):
    if not _check_upload_args(args):
        return
    ucare = create_ucare()
    _file = ucare.upload(args.filename)
    _handle_uploaded_file(_file, args)


def ucare_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='ucare {0}'.format(__version__))

    subparsers = parser.add_subparsers()

    # list
    subparser = subparsers.add_parser('list', help='list all files')
    subparser.set_defaults(func=list_files)
    subparser.add_argument('--page', help='page to show')
    subparser.add_argument('--limit', help='files per page')
    subparser.add_argument('--kept', help='filter kept files',
                           choices=['all', 'true', 'false'])
    subparser.add_argument('--removed', help='filter removed files',
                           choices=['all', 'true', 'false'])

    # get
    subparser = subparsers.add_parser('get', help='get file info')
    subparser.set_defaults(func=get_file)
    subparser.add_argument('path', help='file path')

    # common store and delete args
    waiting_parent = argparse.ArgumentParser(add_help=False)
    group = waiting_parent.add_mutually_exclusive_group()
    group.add_argument(
        '--wait',
        action='store_true',
        default=True,
        dest='wait',
        help='Wait for operation to complete'
    )
    group.add_argument(
        '--nowait',
        action='store_false',
        dest='wait',
        help='Do not wait for operation to complete'
    )

    # store
    subparser = subparsers.add_parser('store',
                                      parents=[waiting_parent],
                                      help='store file')
    subparser.set_defaults(func=store_file)
    subparser.add_argument('path', help='file path')

    # delete
    subparser = subparsers.add_parser('delete',
                                      parents=[waiting_parent],
                                      help='request delete')
    subparser.set_defaults(func=delete_file)
    subparser.add_argument('path', help='file path')

    # common upload args
    upload_parent = argparse.ArgumentParser(add_help=False)
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument('--store',
                       action='store_true',
                       default=False,
                       dest='store',
                       help='Store uploaded file')
    group.add_argument('--nostore',
                       action='store_false',
                       dest='store',
                       help='Do not store uploaded file')
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument('--info',
                       action='store_true',
                       default=False,
                       dest='info',
                       help='Get uploaded file info')
    group.add_argument('--noinfo',
                       action='store_false',
                       dest='info',
                       help='Do not get uploaded file info')
    upload_parent.add_argument('--cdnurl',
                               action='store_true',
                               help='Store file and get CDN url.')

    # upload from url
    subparser = subparsers.add_parser('upload_from_url',
                                      parents=[upload_parent],
                                      help='upload file from url')
    subparser.set_defaults(func=upload_from_url)
    subparser.add_argument('url', help='file url')
    group = subparser.add_mutually_exclusive_group()
    group.add_argument('--wait',
                       action='store_true',
                       default=True,
                       dest='wait',
                       help='Wait for upload status')
    group.add_argument('--nowait',
                       action='store_false',
                       dest='wait',
                       help='Do not wait for upload status')

    # upload
    subparser = subparsers.add_parser('upload',
                                      parents=[upload_parent],
                                      help='upload file')
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
                             ' default: https://api.uploadcare.com/')
    parser.add_argument('--upload_url',
                        help='Upload API url, can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.'
                             ' default: https://upload.uploadcare.com/')
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

    return parser


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
    if getattr(args, 'header', None) is not None:
        for header in args.header:
            name, _, value = header.partition(':')
            custom_headers[name] = value
    if getattr(args, 'cdnurl', False):
        args.store = True
    settings['custom_headers'] = custom_headers


def main():
    args = ucare_argparser().parse_args()
    load_config_from_file('~/.uploadcare')
    load_config_from_file('uploadcare.ini')
    load_config_from_args(args)

    try:
        args.func(args)
    except UploadCareException as e:
        print 'ERROR:'
        print e


if __name__ == '__main__':
    ch = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    main()
