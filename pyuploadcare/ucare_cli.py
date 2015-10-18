#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import time
import argparse
import logging
import pprint
import os
import sys
import re
from math import ceil

import requests
import dateutil.parser
from six.moves import configparser

from . import conf, __version__
from .api_resources import File, FileGroup, FileList
from .exceptions import UploadcareException, TimeoutError, UploadError


pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger('pyuploadcare')
str_settings = (
    'pub_key',
    'secret',
    'api_version',
    'api_base',
    'upload_base',
)
bool_settings = (
    'verify_api_ssl',
    'verify_upload_ssl',
)


def bool_or_none(value):
    return {'true': True, 'false': False}.get(value)


def int_or_none(value):
    return None if value.lower() == 'none' else int(value)


def list_files(arg_namespace):
    files = FileList(
        since=arg_namespace.since,
        until=arg_namespace.until,
        limit=arg_namespace.limit,
        stored=arg_namespace.stored,
        removed=arg_namespace.removed,
    )
    files.constructor = lambda x: x
    pp.pprint(list(files))


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
                raise TimeoutError('timed out trying to store')
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
                raise TimeoutError('timed out trying to delete')
            file_.update_info()
            time.sleep(0.1)


def _check_upload_args(arg_namespace):
    if not conf.secret and (arg_namespace.store or arg_namespace.info):
        pp.pprint('Cannot store or get info without "--secret" key')
        return False
    return True


def _handle_uploaded_file(file_, arg_namespace):
    if arg_namespace.store:
        file_.store()
        pp.pprint('File stored successfully.')

    if arg_namespace.info:
        pp.pprint(file_.info())

    if arg_namespace.cdnurl:
        pp.pprint('CDN url: {0}'.format(file_.cdn_url))


def upload_from_url(arg_namespace):
    if not _check_upload_args(arg_namespace):
        return
    file_from_url = File.upload_from_url(arg_namespace.url)
    pp.pprint(file_from_url)

    if arg_namespace.wait or arg_namespace.store:
        timeout = arg_namespace.timeout
        time_started = time.time()
        while time.time() - time_started < timeout:
            status = file_from_url.update_info()['status']
            if status == 'success':
                break
            if status in ('failed', 'error'):
                raise UploadError(
                    'could not upload file from url: {0}'.format(file_from_url.info())
                )
            time.sleep(1)
        else:
            raise TimeoutError('timed out during upload')

    if arg_namespace.store or arg_namespace.info:
        file_ = file_from_url.get_file()
        if file_ is None:
            pp.pprint('Cannot store or get info.')
            return

        _handle_uploaded_file(file_, arg_namespace)


def upload(arg_namespace):
    if not _check_upload_args(arg_namespace):
        return
    with open(arg_namespace.filename, 'rb') as fh:
        file_ = File.upload(fh)
        _handle_uploaded_file(file_, arg_namespace)


def create_group(arg_namespace):
    files = [File(uuid) for uuid in arg_namespace.paths]
    group = FileGroup.create(files)
    pp.pprint(group)


def sync_files(arg_namespace):
    if arg_namespace.uuids:
        files = (File(uuid) for uuid in arg_namespace.uuids)
    else:
        files = FileList()

    session = requests.Session()

    for f in files:
        if arg_namespace.effects:
            f.default_effects = arg_namespace.effects

        local_filepath = build_filepath(arg_namespace.path, f)
        dirname = os.path.dirname(local_filepath)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.exists(local_filepath) and not arg_namespace.replace:
            pp.pprint(
                'File `{0}` already exists. '
                'To override it use `--replace` option'.format(
                    local_filepath))
            continue

        url = f.cdn_url
        response = session.get(url, stream=True, verify=conf.verify_api_ssl)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            pp.pprint(('Can\'t download file: `{0}`. '
                       'Origin error: {1}').format(url, e))
            continue

        save_file_locally(local_filepath, response, f.size())


PATTERNS_REGEX = re.compile(r'(\${\w+})')
PATTERNS_MAPPING = {
    '${uuid}': lambda f: f.uuid,
    '${filename}': lambda f: f.filename(),
    '${effects}': lambda f: f.default_effects,
    '${ext}': lambda f: '.{0}'.format(f.info()["image_info"]["format"]).lower()
}
DEFAULT_PATTERN_FILENAME = '${uuid}${ext}'


def build_filepath(path, file_):
    if not PATTERNS_REGEX.findall(path):
        path = os.path.join(path, DEFAULT_PATTERN_FILENAME)

    def _replace(mobj):
        pattern_name = mobj.group(0)
        if pattern_name in PATTERNS_MAPPING:
            pattern = PATTERNS_MAPPING[pattern_name]
            return pattern(file_)
        return pattern_name

    return os.path.normpath(PATTERNS_REGEX.sub(_replace, path))


def save_file_locally(fname, response, size):
    chunk_size = 1024
    with open(fname, 'wb') as lf:
        for chunk in bar(response.iter_content(chunk_size),
                         ceil(size / float(chunk_size)),
                         fname):
            lf.write(chunk)


def bar(iter_content, parts, title=''):
    parts = float(parts)
    cells = 10
    progress = 0
    step = cells / parts

    draw = lambda progress: sys.stdout.write(
        '\r[{0:10}] {1:.2f}% {2}'.format(
            '#'*int(progress), progress * cells, title))

    for chunk in iter_content:
        yield chunk

        progress += step
        draw(progress)
        sys.stdout.flush()

    draw(cells)
    print('')


def ucare_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='ucare {0}'.format(__version__))

    subparsers = parser.add_subparsers()

    # list
    subparser = subparsers.add_parser('list', help='list all files')
    subparser.set_defaults(func=list_files)
    subparser.add_argument('--since', help='show files uploaded since',
                           type=dateutil.parser.parse)
    subparser.add_argument('--until', help='show files uploaded until',
                           type=dateutil.parser.parse)
    subparser.add_argument('--limit', help='files to show', default=100,
                           type=int_or_none)
    subparser.add_argument('--stored', help='filter stored files',
                           choices=[True, False, None],
                           type=bool_or_none, default=None)
    subparser.add_argument('--removed', help='filter removed files',
                           choices=[True, False, None],
                           type=bool_or_none, default=False)

    # get
    subparser = subparsers.add_parser('get', help='get file info')
    subparser.set_defaults(func=get_file)
    subparser.add_argument('path', help='file path')

    # common store and delete args
    waiting_parent = argparse.ArgumentParser(add_help=False)
    waiting_parent.add_argument(
        '--timeout',
        type=int,
        dest='timeout',
        default=5,
        help='Set wait seconds until operation completed.'
             ' Default value is 5 seconds')
    group = waiting_parent.add_mutually_exclusive_group()
    group.add_argument(
        '--wait',
        action='store_true',
        default=True,
        dest='wait',
        help='Wait for operation to be completed'
    )
    group.add_argument(
        '--nowait',
        action='store_false',
        dest='wait',
        help='Do not wait for operation to be completed'
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
    group.add_argument(
        '--store',
        action='store_true',
        default=False,
        dest='store',
        help='Store uploaded file')
    group.add_argument(
        '--nostore',
        action='store_false',
        dest='store',
        help='Do not store uploaded file')
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument(
        '--info',
        action='store_true',
        default=False,
        dest='info',
        help='Get uploaded file info')
    group.add_argument(
        '--noinfo',
        action='store_false',
        dest='info',
        help='Do not get uploaded file info')
    upload_parent.add_argument(
        '--cdnurl',
        action='store_true',
        help='Store file and get CDN url.')

    # upload from url
    subparser = subparsers.add_parser('upload_from_url',
                                      parents=[upload_parent],
                                      help='upload file from url')
    subparser.set_defaults(func=upload_from_url)
    subparser.add_argument('url', help='file url')
    subparser.add_argument(
        '--timeout',
        type=int,
        dest='timeout',
        default=30,
        help='Set wait seconds file uploading from url.'
             ' Default value is 30 seconds')
    group = subparser.add_mutually_exclusive_group()
    group.add_argument(
        '--wait',
        action='store_true',
        default=True,
        dest='wait',
        help='Wait for upload status')
    group.add_argument(
        '--nowait',
        action='store_false',
        dest='wait',
        help='Do not wait for upload status')

    # upload
    subparser = subparsers.add_parser('upload', parents=[upload_parent],
                                      help='upload file')
    subparser.set_defaults(func=upload)
    subparser.add_argument('filename', help='filename')

    # Create file group.
    subparser = subparsers.add_parser('create_group', help='create file group')
    subparser.set_defaults(func=create_group)
    subparser.add_argument('paths', nargs='+', help='file paths')

    # Sync files
    subparser = subparsers.add_parser('sync', help='sync files')
    subparser.set_defaults(func=sync_files)
    subparser.add_argument('path', nargs='?', help=(
        'Local path. It can contains special patterns like: {0} '
        'Default is {1}'.format(
            ' '.join(PATTERNS_MAPPING.keys()),
            DEFAULT_PATTERN_FILENAME)
    ), default='.')
    subparser.add_argument('--replace', help='replace exists files',
                           default=False, action='store_true')
    subparser.add_argument('--uuids', nargs='+',
                           help='list of file\'s uuids for sync',)
    subparser.add_argument('--effects', help=(
        'apply effects for synced images. For more information look at: '
        'https://uploadcare.com/documentation/cdn/'
    ))

    # common arguments
    parser.add_argument(
        '--pub_key',
        help='API key, if not set is read from uploadcare.ini'
             ' and ~/.uploadcare config files')
    parser.add_argument(
        '--secret',
        help='API secret, if not set is read from uploadcare.ini'
             ' and ~/.uploadcare config files')
    parser.add_argument(
        '--api_base',
        help='API url, can be read from uploadcare.ini'
             ' and ~/.uploadcare config files.'
             ' Default value is {0}'.format(conf.api_base))
    parser.add_argument(
        '--upload_base',
        help='Upload API url, can be read from uploadcare.ini'
             ' and ~/.uploadcare config files.'
             ' Default value is {0}'.format(conf.upload_base))
    parser.add_argument(
        '--no_check_upload_certificate',
        action='store_true',
        help="Don't check the uploading API server certificate."
             ' Can be read from uploadcare.ini'
             ' and ~/.uploadcare config files.')
    parser.add_argument(
        '--no_check_api_certificate',
        action='store_true',
        help="Don't check the REST API server certificate."
             ' Can be read from uploadcare.ini'
             ' and ~/.uploadcare config files.')
    parser.add_argument(
        '--api_version',
        help='API version, can be read from uploadcare.ini'
             ' and ~/.uploadcare config files.'
             ' Default value is {0}'.format(conf.api_version))

    return parser


def load_config_from_file(filename):
    filename = os.path.expanduser(filename)
    if not os.path.exists(filename):
        return

    config = configparser.RawConfigParser()
    config.read(filename)

    for name in str_settings:
        try:
            setattr(conf, name, config.get('ucare', name))
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass
    for name in bool_settings:
        try:
            setattr(conf, name, config.getboolean('ucare', name))
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass


def load_config_from_args(arg_namespace):
    for name in str_settings:
        arg = getattr(arg_namespace, name, None)
        if arg is not None:
            setattr(conf, name, arg)

    if arg_namespace and arg_namespace.no_check_upload_certificate:
        conf.verify_upload_ssl = False
    if arg_namespace and arg_namespace.no_check_api_certificate:
        conf.verify_api_ssl = False

    if getattr(arg_namespace, 'cdnurl', False):
        arg_namespace.store = True


def main(arg_namespace=None,
         config_file_names=('~/.uploadcare', 'uploadcare.ini')):
    if arg_namespace is None:
        arg_namespace = ucare_argparser().parse_args()

    if config_file_names:
        for file_name in config_file_names:
            load_config_from_file(file_name)
    load_config_from_args(arg_namespace)

    if hasattr(arg_namespace, 'func'):
        try:
            arg_namespace.func(arg_namespace)
        except UploadcareException as exc:
            pp.pprint('ERROR: {0}'.format(exc))


if __name__ == '__main__':
    ch = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    main()
