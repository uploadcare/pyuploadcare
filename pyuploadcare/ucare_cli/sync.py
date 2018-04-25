# coding: utf-8
from __future__ import unicode_literals
import os
import re
import time
import hashlib
from math import ceil

import requests
from six import text_type
from six.moves import cPickle as pickle
from dateutil import parser

from pyuploadcare import conf
from pyuploadcare.api import _build_user_agent, rest_request
from pyuploadcare.api_resources import FileList, File
from pyuploadcare.ucare_cli.utils import (
    pprint, promt, int_or_none, bool_or_none, bar
)


def sync_files(arg_namespace):
    session = requests.Session()
    session.headers.update({'User-Agent': _build_user_agent()})

    def _get(url, max_retry=3):
        response = None

        for i in range(max_retry):
            try:
                response = session.get(url, stream=True,
                                       verify=conf.verify_api_ssl)
            except requests.exceptions.ConnectionError as e:
                pprint('Connection Error: {0}'.format(e))
                pprint('Retry..')
                time.sleep(i ** 2)
                continue
            else:
                break

        if response is None:
            pprint('Can\'t fetch URL: {0}'.format(url))
            pprint('Skip it.')
            return

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            pprint(('Can\'t download file: `{0}`. '
                    'Origin error: {1}').format(url, e))
            return

        return response

    if arg_namespace.starting_point:
        ordering_field = (arg_namespace.ordering or '').lstrip('-')
        if ordering_field in ('', 'datetime_uploaded'):
            arg_namespace.starting_point = parser.parse(
                arg_namespace.starting_point)

    kwargs = dict(uuids=arg_namespace.uuids or None)
    if kwargs['uuids'] is None:
        kwargs.update(dict(
            starting_point=arg_namespace.starting_point,
            ordering=arg_namespace.ordering,
            limit=arg_namespace.limit,
            stored=arg_namespace.stored,
            removed=arg_namespace.removed,
            request_limit=arg_namespace.request_limit,
        ))

    with SyncSession(TrackedFileList(**kwargs)) as files:
        for f in files:
            if f.is_image() and arg_namespace.effects:
                f.default_effects = arg_namespace.effects.lstrip('-/')

            local_filepath = build_filepath(arg_namespace.path, f)
            dirname = os.path.dirname(local_filepath)

            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)

            if os.path.exists(local_filepath) and not arg_namespace.replace:
                pprint('File `{0}` already exists. '
                       'To override it use `--replace` option'
                       .format(local_filepath))
                continue

            url = f.cdn_url
            response = _get(url)

            if response:
                save_file_locally(local_filepath, response, f.size())


PATTERNS_REGEX = re.compile(r'(\${\w+})')
PATTERNS_MAPPING = {
    '${uuid}': lambda f: f.uuid,
    '${filename}': lambda f: f.filename(),
    '${effects}': lambda f: f.default_effects,
    '${ext}': lambda f: os.path.splitext(f.filename() or '')[-1],
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


class SyncSession(object):
    """ Provides an ability to save current state of iteration if any errors
    happened during iteration. After that is possible to restore this state
    and continue from that point.
    """
    def __init__(self, file_list):
        parts = text_type(file_list.__dict__)
        self.session = file_list
        self.signature = hashlib.md5(parts.encode('utf-8')).hexdigest()
        self.session_filepath = os.path.join(
            os.path.expanduser('~'),
            '.{0}.sync'.format(self.signature))

        # If the serialized session is exists load it and set as current
        if os.path.exists(self.session_filepath):
            if promt('Continue last sync?'):
                with open(self.session_filepath, 'rb') as f:
                    self.session = pickle.load(f)
                    return

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        if all(args):
            with open(self.session_filepath, 'wb') as f:
                pickle.dump(self.session, f)
            return False

        # Iteration is complete without errors.
        # Let's delete serialized session if exists.
        if os.path.exists(self.session_filepath):
            try:
                os.remove(self.session_filepath)
            except OSError:
                pass

        return True


class TrackedFileList(FileList):
    """ Transparently iterate over provided list of UUIDs and all list
    of files of the user. Saves current state of iteration.
    """
    def __init__(self, *args, **kwargs):
        self.uuids = kwargs.pop('uuids', None)
        self.handled_uuids = []
        self.last_page_url = None
        super(TrackedFileList, self).__init__(*args, **kwargs)

    def __iter__(self):
        if self.uuids:
            return self.iter_uuids()

        return self.iter_urls(
            self.last_page_url or self.api_url(), self.limit)

    def iter_uuids(self):
        for uuid in self.uuids:
            if uuid in self.handled_uuids:
                continue
            yield File(uuid)
            self.handled_uuids.append(uuid)

    def iter_urls(self, next_url, limit=None):
        while next_url and limit != 0:
            self.last_page_url = next_url

            result = rest_request('GET', next_url)
            working_set = result['results']
            next_url = result['next']

            for item in working_set:
                obj = self.constructor(item)

                if obj.uuid not in self.handled_uuids:
                    yield obj
                    self.handled_uuids.append(obj.uuid)

                if limit is not None:
                    limit -= 1
                    if limit == 0:
                        return

            self.handled_uuids = []


def add_sync_files_parser(subparsers):
    subparser = subparsers.add_parser('sync', help='sync files')
    subparser.set_defaults(func=sync_files)
    subparser.add_argument('path', nargs='?', help=(
        'Local path. It can contains special patterns like: {0} '
        'Default is {1}'.format(
            ' '.join(PATTERNS_MAPPING.keys()),
            DEFAULT_PATTERN_FILENAME)
    ), default='.')
    subparser.add_argument(
        '--starting_point',
        help='a starting point for filtering files',
        action='store')
    subparser.add_argument(
        '--ordering',
        help='specify the way the files should be sorted',
        action='store')
    subparser.add_argument('--limit', help='files to show', default=100,
                           type=int_or_none)
    subparser.add_argument('--request_limit', help='files per request',
                           default=100, type=int_or_none)
    subparser.add_argument('--stored', help='filter stored files',
                           choices=[True, False, None],
                           type=bool_or_none, default=None)
    subparser.add_argument('--removed', help='filter removed files',
                           choices=[True, False, None],
                           type=bool_or_none, default=False)
    subparser.add_argument('--replace', help='replace exists files',
                           default=False, action='store_true')
    subparser.add_argument('--uuids', nargs='+',
                           help='list of file\'s uuids for sync',)
    subparser.add_argument('--effects', help=(
        'apply effects for synced images.'
        'Note that effects will apply to images only.'
        'For more information look at: '
        'https://uploadcare.com/docs/processing/image/  '
        'Example: --effects=resize/200x/-/rotate/90/'
    ))
    return subparser
