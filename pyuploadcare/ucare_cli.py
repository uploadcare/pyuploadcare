#!/usr/bin/python
# encoding: utf-8
import argparse
import urlparse
import urllib
import logging
import pprint
import ConfigParser
import os.path

from pyuploadcare import __version__, conf
from pyuploadcare.exceptions import UploadcareException
from pyuploadcare.file import File
from pyuploadcare.api import RESTClient


pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger('pyuploadcare')
available_settings = [
    'pub_key',
    'secret',
    'api_version',
    'api_base',
    'upload_base',
]


def list_files(args=None):
    query = {}
    for name in ['page', 'limit', 'kept', 'removed']:
        arg = getattr(args, name)
        if arg is not None:
            query[name] = arg
    q = urllib.urlencode(query)
    url = urlparse.urlunsplit(['', '', '/files/', q, ''])

    pp.pprint(RESTClient.make_request('GET', url))


def get_file(args):
    pp.pprint(File(args.path).info())


def store_file(args):
    File(args.path).store(wait=args.wait)


def delete_file(args):
    File(args.path).delete(wait=args.wait)


def _check_upload_args(args):
    if not args.secret and (args.store or args.info):
        print 'Cannot store or get info without "--secret" key'
        return False
    return True


def _handle_uploaded_file(file_, args):
    if args.store:
        file_.store(wait=True)
        print 'File stored successfully.'

    if args.info:
        pp.pprint(file_.info())

    if args.cdnurl:
        print 'CDN url: {0}'.format(file_.cdn_url)


def upload_from_url(args):
    if not _check_upload_args(args):
        return
    file_from_url = File.upload_from_url(args.url,
                                         wait=args.wait or args.store)
    print file_from_url

    if args.store or args.info:
        file_ = file_from_url.get_file()
        if file_ is None:
            print 'Cannot store or get info.'
            return

        _handle_uploaded_file(file_, args)


def upload(args):
    if not _check_upload_args(args):
        return
    with open(args.filename, 'rb') as fh:
        file_ = File.upload(fh)
        _handle_uploaded_file(file_, args)


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
    parser.add_argument('--api_base',
                        help='API url, can be read from uploadcare.ini'
                             ' and ~/.uploadcare config files.'
                             ' default: https://api.uploadcare.com/')
    parser.add_argument('--upload_base',
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

    return parser


def load_config_from_file(filename):
    filename = os.path.expanduser(filename)
    if not os.path.exists(filename):
        return

    config = ConfigParser.RawConfigParser()
    config.read(filename)

    for name in available_settings:
        try:
            setattr(conf, name, config.get('ucare', name))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            pass


def load_config_from_args(args):
    for name in available_settings:
        arg = getattr(args, name, None)
        if arg is not None:
            setattr(conf, name, arg)
    if getattr(args, 'cdnurl', False):
        args.store = True


def main():
    args = ucare_argparser().parse_args()
    load_config_from_file('~/.uploadcare')
    load_config_from_file('uploadcare.ini')
    load_config_from_args(args)

    try:
        args.func(args)
    except UploadcareException as exc:
        print 'ERROR: {0}'.format(exc)


if __name__ == '__main__':
    ch = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    main()
