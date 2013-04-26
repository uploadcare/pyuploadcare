#!/usr/bin/python
# encoding: utf-8
import time
import argparse
import urlparse
import urllib
import logging
import pprint
import ConfigParser
import os.path

from . import conf, __version__
from .api_resources import File, FileGroup
from .exceptions import UploadcareException, TimeoutError, UploadError
from .api import rest_request


pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger(u'pyuploadcare')
str_settings = (
    u'pub_key',
    u'secret',
    u'api_version',
    u'api_base',
    u'upload_base',
)
bool_settings = (
    u'verify_api_ssl',
    u'verify_upload_ssl',
)


def list_files(arg_namespace=None):
    query = {}
    for name in [u'page', u'limit', u'kept', u'removed']:
        arg = getattr(arg_namespace, name)
        if arg is not None:
            query[name] = arg
    q = urllib.urlencode(query)
    url = urlparse.urlunsplit([u'', u'', u'files/', q, u''])

    pp.pprint(rest_request(u'GET', url))


def get_file(arg_namespace):
    pp.pprint(File(arg_namespace.path).info())


def store_file(arg_namespace):
    file_ = File(arg_namespace.path)
    file_.store()

    if arg_namespace.wait:
        timeout = arg_namespace.timeout
        time_started = time.time()
        while not file_.is_stored():
            if time.time() - time_started > timeout:
                raise TimeoutError(u'timed out trying to store')
            file_.update_info()
            time.sleep(0.1)


def delete_file(arg_namespace):
    file_ = File(arg_namespace.path)
    file_.delete()

    if arg_namespace.wait:
        timeout = arg_namespace.timeout
        time_started = time.time()
        while not file_.is_removed():
            if time.time() - time_started > timeout:
                raise TimeoutError(u'timed out trying to delete')
            file_.update_info()
            time.sleep(0.1)


def _check_upload_args(arg_namespace):
    if not conf.secret and (arg_namespace.store or arg_namespace.info):
        pp.pprint(u'Cannot store or get info without "--secret" key')
        return False
    return True


def _handle_uploaded_file(file_, arg_namespace):
    if arg_namespace.store:
        file_.store()
        pp.pprint(u'File stored successfully.')

    if arg_namespace.info:
        pp.pprint(file_.info())

    if arg_namespace.cdnurl:
        pp.pprint(u'CDN url: {0}'.format(file_.cdn_url))


def upload_from_url(arg_namespace):
    if not _check_upload_args(arg_namespace):
        return
    file_from_url = File.upload_from_url(arg_namespace.url)
    pp.pprint(file_from_url)

    if arg_namespace.wait or arg_namespace.store:
        timeout = arg_namespace.timeout
        time_started = time.time()
        while time.time() - time_started < timeout:
            status = file_from_url.update_info()[u'status']
            if status == u'success':
                break
            if status in (u'failed', u'error'):
                raise UploadError(
                    u'could not upload file from url: {0}'.format(file_from_url.info())
                )
            time.sleep(1)
        else:
            raise TimeoutError(u'timed out during upload')

    if arg_namespace.store or arg_namespace.info:
        file_ = file_from_url.get_file()
        if file_ is None:
            pp.pprint(u'Cannot store or get info.')
            return

        _handle_uploaded_file(file_, arg_namespace)


def upload(arg_namespace):
    if not _check_upload_args(arg_namespace):
        return
    with open(arg_namespace.filename, u'rb') as fh:
        file_ = File.upload(fh)
        _handle_uploaded_file(file_, arg_namespace)


def create_group(arg_namespace):
    files = [File(uuid) for uuid in arg_namespace.paths]
    group = FileGroup.create(files)
    pp.pprint(group)


def ucare_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(u'--version', action=u'version',
                        version=u'ucare {0}'.format(__version__))

    subparsers = parser.add_subparsers()

    # list
    subparser = subparsers.add_parser(u'list', help=u'list all files')
    subparser.set_defaults(func=list_files)
    subparser.add_argument(u'--page', help=u'page to show')
    subparser.add_argument(u'--limit', help=u'files per page')
    subparser.add_argument(u'--kept', help=u'filter kept files',
                           choices=[u'all', u'true', u'false'])
    subparser.add_argument(u'--removed', help=u'filter removed files',
                           choices=[u'all', u'true', u'false'])

    # get
    subparser = subparsers.add_parser(u'get', help=u'get file info')
    subparser.set_defaults(func=get_file)
    subparser.add_argument(u'path', help=u'file path')

    # common store and delete args
    waiting_parent = argparse.ArgumentParser(add_help=False)
    waiting_parent.add_argument(
        u'--timeout',
        type=int,
        dest=u'timeout',
        default=5,
        help=u'Set wait seconds until operation completed.'
             u' Default value is 5 seconds')
    group = waiting_parent.add_mutually_exclusive_group()
    group.add_argument(
        u'--wait',
        action=u'store_true',
        default=True,
        dest=u'wait',
        help=u'Wait for operation to be completed'
    )
    group.add_argument(
        u'--nowait',
        action=u'store_false',
        dest=u'wait',
        help=u'Do not wait for operation to be completed'
    )

    # store
    subparser = subparsers.add_parser(u'store',
                                      parents=[waiting_parent],
                                      help=u'store file')
    subparser.set_defaults(func=store_file)
    subparser.add_argument(u'path', help=u'file path')

    # delete
    subparser = subparsers.add_parser(u'delete',
                                      parents=[waiting_parent],
                                      help=u'request delete')
    subparser.set_defaults(func=delete_file)
    subparser.add_argument(u'path', help=u'file path')

    # common upload args
    upload_parent = argparse.ArgumentParser(add_help=False)
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument(
        u'--store',
        action=u'store_true',
        default=False,
        dest=u'store',
        help=u'Store uploaded file')
    group.add_argument(
        u'--nostore',
        action=u'store_false',
        dest=u'store',
        help=u'Do not store uploaded file')
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument(
        u'--info',
        action=u'store_true',
        default=False,
        dest=u'info',
        help=u'Get uploaded file info')
    group.add_argument(
        u'--noinfo',
        action=u'store_false',
        dest=u'info',
        help=u'Do not get uploaded file info')
    upload_parent.add_argument(
        u'--cdnurl',
        action=u'store_true',
        help=u'Store file and get CDN url.')

    # upload from url
    subparser = subparsers.add_parser(u'upload_from_url',
                                      parents=[upload_parent],
                                      help=u'upload file from url')
    subparser.set_defaults(func=upload_from_url)
    subparser.add_argument(u'url', help=u'file url')
    subparser.add_argument(
        u'--timeout',
        type=int,
        dest=u'timeout',
        default=30,
        help=u'Set wait seconds file uploading from url.'
             u' Default value is 30 seconds')
    group = subparser.add_mutually_exclusive_group()
    group.add_argument(
        u'--wait',
        action=u'store_true',
        default=True,
        dest=u'wait',
        help=u'Wait for upload status')
    group.add_argument(
        u'--nowait',
        action=u'store_false',
        dest=u'wait',
        help=u'Do not wait for upload status')

    # upload
    subparser = subparsers.add_parser(u'upload', parents=[upload_parent],
                                      help=u'upload file')
    subparser.set_defaults(func=upload)
    subparser.add_argument(u'filename', help=u'filename')

    # Create file group.
    subparser = subparsers.add_parser(u'create_group', help=u'create file group')
    subparser.set_defaults(func=create_group)
    subparser.add_argument(u'paths', nargs=u'+', help=u'file paths')

    # common arguments
    parser.add_argument(
        u'--pub_key',
        help=u'API key, if not set is read from uploadcare.ini'
             u' and ~/.uploadcare config files')
    parser.add_argument(
        u'--secret',
        help=u'API secret, if not set is read from uploadcare.ini'
             u' and ~/.uploadcare config files')
    parser.add_argument(
        u'--api_base',
        help=u'API url, can be read from uploadcare.ini'
             u' and ~/.uploadcare config files.'
             u' Default value is {0}'.format(conf.api_base))
    parser.add_argument(
        u'--upload_base',
        help=u'Upload API url, can be read from uploadcare.ini'
             u' and ~/.uploadcare config files.'
             u' Default value is {0}'.format(conf.upload_base))
    parser.add_argument(
        u'--no_check_upload_certificate',
        action=u'store_true',
        help=u"Don't check the uploading API server certificate."
             u' Can be read from uploadcare.ini'
             u' and ~/.uploadcare config files.')
    parser.add_argument(
        u'--no_check_api_certificate',
        action=u'store_true',
        help=u"Don't check the REST API server certificate."
             u' Can be read from uploadcare.ini'
             u' and ~/.uploadcare config files.')
    parser.add_argument(
        u'--api_version',
        help=u'API version, can be read from uploadcare.ini'
             u' and ~/.uploadcare config files.'
             u' Default value is {0}'.format(conf.api_version))

    return parser


def load_config_from_file(filename):
    filename = os.path.expanduser(filename)
    if not os.path.exists(filename):
        return

    config = ConfigParser.RawConfigParser()
    config.read(filename)

    for name in str_settings:
        try:
            setattr(conf, name, config.get(u'ucare', name))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            pass
    for name in bool_settings:
        try:
            setattr(conf, name, config.getboolean(u'ucare', name))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            pass


def load_config_from_args(arg_namespace):
    for name in str_settings:
        arg = getattr(arg_namespace, name, None)
        if arg is not None:
            setattr(conf, name, arg)

    if arg_namespace.no_check_upload_certificate:
        conf.verify_upload_ssl = False
    if arg_namespace.no_check_api_certificate:
        conf.verify_api_ssl = False

    if getattr(arg_namespace, u'cdnurl', False):
        arg_namespace.store = True


def main(arg_namespace=None, config_file_names=None):
    if config_file_names:
        for file_name in config_file_names:
            load_config_from_file(file_name)
    load_config_from_args(arg_namespace)

    try:
        arg_namespace.func(arg_namespace)
    except UploadcareException as exc:
        pp.pprint(u'ERROR: {0}'.format(exc))


if __name__ == u'__main__':
    ch = logging.StreamHandler()
    fmt = logging.Formatter(u'%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    main(arg_namespace=ucare_argparser().parse_args(),
         config_file_names=(u'~/.uploadcare', u'uploadcare.ini'))
