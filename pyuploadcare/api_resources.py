# coding: utf-8
from __future__ import unicode_literals, division
import re
import logging
import time
from itertools import islice
from datetime import date, datetime

import dateutil.parser
import six

if six.PY3:
    from urllib.parse import urlencode
    from collections.abc import Iterable
else:
    from urllib import urlencode
    from collections import Iterable

from . import conf
from .api import rest_request, uploading_request
from .exceptions import InvalidParamError, APIError, UploadError, TimeoutError


logger = logging.getLogger("pyuploadcare")


RE_UUID = '[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}'
RE_UUID_REGEX = re.compile('^{0}$'.format(RE_UUID))
RE_EFFECTS = '(?:[^/]+/)+'  # -/resize/(200x300/)*
UUID_WITH_EFFECTS_REGEX = re.compile('''
    /?
    (?P<uuid>{uuid})  # required
    (?:
        /
        (?:-/(?P<effects>{effects}))?
        ([^/]*)  # filename
    )?
$'''.format(uuid=RE_UUID, effects=RE_EFFECTS), re.VERBOSE)


class File(object):
    """File resource for working with user-uploaded files.

    It can take file UUID or group CDN url::

        >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
        >>> file_.cdn_url
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/
        >>> print File('https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/')
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/

    """

    def __init__(self, cdn_url_or_file_id):
        matches = UUID_WITH_EFFECTS_REGEX.search(cdn_url_or_file_id)

        if not matches:
            raise InvalidParamError("Couldn't find UUID")

        self._uuid = matches.groupdict()['uuid']
        self.default_effects = matches.groupdict()['effects']

        self._info_cache = None

    def __repr__(self):
        return '<uploadcare.File {uuid}>'.format(uuid=self.uuid)

    def __str__(self):
        return self.cdn_url

    def _build_effects(self, effects=''):
        if self.default_effects is not None:
            fmt = '{head}-/{tail}' if effects else '{head}'
            effects = fmt.format(head=self.default_effects,
                                 tail=effects)
        return effects

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        match = RE_UUID_REGEX.match(value)

        if not match:
            raise InvalidParamError('Invalid UUID: {0}'.format(value))

        self._uuid = match.group(0)

    @property
    def _api_uri(self):
        return 'files/{0}/'.format(self.uuid)

    @property
    def _api_storage_uri(self):
        return 'files/{0}/storage/'.format(self.uuid)

    def cdn_path(self, effects=None):
        ptn = '{uuid}/-/{effects}' if effects else '{uuid}/'
        return ptn.format(
            uuid=self.uuid,
            effects=effects
        )

    @property
    def cdn_url(self):
        """Returns file's CDN url.

        Usage example::

            >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> file_.cdn_url
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/

        You can set default effects::

            >>> file_.default_effects = 'effect/flip/-/effect/mirror/'
            >>> file_.cdn_url
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/-/effect/mirror/

        """
        return '{cdn_base}{path}'.format(cdn_base=conf.cdn_base,
                                         path=self.cdn_path(self.default_effects))

    def info(self):
        """Returns all available file information as ``dict``.

        First time it makes API request to get file information and keeps it
        for further using.

        """
        if self._info_cache is None:
            self.update_info()
        return self._info_cache

    def update_info(self):
        """Updates and returns file information by requesting Uploadcare API.
        """
        self._info_cache = rest_request('GET', self._api_uri)
        return self._info_cache

    def filename(self):
        """Returns original file name, e.g. ``"olympia.jpg"``.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('original_filename')

    def datetime_stored(self):
        """Returns file's store aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        if self.info().get('datetime_stored'):
            return dateutil.parser.parse(self.info()['datetime_stored'])

    def datetime_removed(self):
        """Returns file's remove aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        if self.info().get('datetime_removed'):
            return dateutil.parser.parse(self.info()['datetime_removed'])

    def datetime_uploaded(self):
        """Returns file's upload aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        if self.info().get('datetime_uploaded'):
            return dateutil.parser.parse(self.info()['datetime_uploaded'])

    def is_stored(self):
        """Returns ``True`` if file is stored.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('datetime_stored') is not None

    def is_removed(self):
        """Returns ``True`` if file is removed.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('datetime_removed') is not None

    def is_image(self):
        """Returns ``True`` if the file is an image.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('is_image')

    def is_ready(self):
        """Returns ``True`` if the file is fully uploaded on S3.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('is_ready')

    def size(self):
        """Returns the file size in bytes.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('size')

    def mime_type(self):
        """Returns the file MIME type, e.g. ``"image/png"``.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('mime_type')

    def store(self):
        """Stores file by requesting Uploadcare API.

        Uploaded files do not immediately appear on Uploadcare CDN.
        Let's consider steps until file appears on CDN:

        - first file is uploaded into https://upload.uploadcare.com/;
        - after that file is available by API and its ``is_public``,
          ``is_ready`` are ``False``. Now you can store it;
        - ``is_ready`` will be ``True`` when file will be fully uploaded
          on S3.

        """
        self._info_cache = rest_request('PUT', self._api_storage_uri)

    def copy(self, effects=None, target=None):
        """Creates a File Copy on Uploadcare or Custom Storage.
        
        File.copy method is deprecated and will be removed in 4.0.0.
        Please use `create_local_copy` and `create_remote_copy` instead.

        Args:
            - effects:
                Adds CDN image effects. If ``self.default_effects`` property
                is set effects will be combined with default effects.
            - target:
                Name of a custom storage connected to your project.
                Uploadcare storage is used if target is absent.

        """
        warning = """File.copy method is deprecated and will be
            removed in 4.0.0.
            Please use `create_local_copy`
            and `create_remote_copy` instead.
        """
        logger.warn('API Warning: {0}'.format(warning))

        if target is not None:
            return self.create_remote_copy(target, effects)
        else:
            return self.create_local_copy(effects)

    def create_local_copy(self, effects=None, store=None):
        """Creates a Local File Copy on Uploadcare Storage.

        Args:
            - effects:
                Adds CDN image effects. If ``self.default_effects`` property
                is set effects will be combined with default effects.
            - store:
                If ``store`` option is set to False the copy of your file will
                be deleted in 24 hour period after the upload.
                Works only if `autostore` is enabled in the project.

        """
        effects = self._build_effects(effects)
        store = store or ''
        data = {
            'source': self.cdn_path(effects)
        }
        if store:
            data['store'] = store
        return rest_request('POST', 'files/', data=data)

    def create_remote_copy(self, target, effects=None, make_public=None,
                           pattern=None):
        """Creates file copy in remote storage.

        Args:
            - target:
                Name of a custom storage connected to the project.
            - effects:
                Adds CDN image effects to ``self.default_effects`` if any.
            - make_public:
                To forbid public from accessing your files on the storage set
                ``make_public`` option to be False.
                Default value is None. Files have public access by default.
            - pattern:
                Specify ``pattern`` option to set S3 object key name.
                Takes precedence over pattern set in project settings.
                If neither is specified defaults to
                `${uuid}/${filename}${effects}${ext}`.

        For more information on each of the options above please refer to
        REST API docs https://uploadcare.com/docs/api_reference/rest/accessing_files/.

        Following example copies a file to custom storage named ``samplefs``:

             >>> file = File('e8ebfe20-8c11-4a94-9b40-52ecad7d8d1a')
             >>> file.create_remote_copy(target='samplefs',
             >>>                         make_public=True,
             >>>                         pattern='${uuid}/${filename}${ext}')

        Now custom storage ``samplefs`` contains publicly available file
        with original filename billmurray.jpg in
        in the directory named ``e8ebfe20-8c11-4a94-9b40-52ecad7d8d1a``.

        """
        effects = self._build_effects(effects)
        data = {
            'source': self.cdn_path(effects),
            'target': target
        }

        if make_public is not None:
            data['make_public'] = make_public
        if pattern is not None:
            data['pattern'] = pattern
        return rest_request('POST', 'files/', data=data)

    def delete(self):
        """Deletes file by requesting Uploadcare API."""
        self._info_cache = rest_request('DELETE', self._api_uri)

    @classmethod
    def construct_from(cls, file_info):
        """Constructs ``File`` instance from file information.

        For example you have result of
        ``/files/1921953c-5d94-4e47-ba36-c2e1dd165e1a/`` API request::

            >>> file_info = {
                    # ...
                    'uuid': '1921953c-5d94-4e47-ba36-c2e1dd165e1a',
                    # ...
                }
            >>> File.construct_from(file_info)
            <uploadcare.File 1921953c-5d94-4e47-ba36-c2e1dd165e1a>

        """
        file_ = cls(file_info['uuid'])
        file_.default_effects = file_info.get('default_effects')
        file_._info_cache = file_info
        return file_

    @classmethod
    def upload(cls, file_obj, store=None):
        """Uploads a file and returns ``File`` instance.

        Args:
            - file_obj: file object to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings

        Returns:
            ``File`` instance

        """
        if store is None:
            store = 'auto'
        elif store:
            store = '1'
        else:
            store = '0'

        data = {
            'UPLOADCARE_STORE': store,
        }

        files = uploading_request('POST', 'base/', data=data,
                                  files={'file': file_obj})
        file_ = cls(files['file'])
        return file_

    @classmethod
    def upload_from_url(cls, url, store=None, filename=None):
        """Uploads file from given url and returns ``FileFromUrl`` instance.

        Args:
            - url (str): URL of file to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - filename (Optional[str]): Name of the uploaded file. If this not
                specified the filename will be obtained from response headers
                or source URL. Defaults to None.

        Returns:
            ``FileFromUrl`` instance

        """
        if store is None:
            store = 'auto'
        elif store:
            store = '1'
        else:
            store = '0'

        data = {
            'source_url': url,
            'store': store,
        }
        if filename:
            data['filename'] = filename

        result = uploading_request('POST', 'from_url/',
                                   data=data)
        if 'token' not in result:
            raise APIError(
                'could not find token in result: {0}'.format(result)
            )
        file_from_url = cls.FileFromUrl(result['token'])
        return file_from_url

    @classmethod
    def upload_from_url_sync(cls, url, timeout=30, interval=0.3,
                             until_ready=False, store=None, filename=None):
        """Uploads file from given url and returns ``File`` instance.

        Args:
            - url (str): URL of file to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - filename (Optional[str]): Name of the uploaded file. If this not
                specified the filename will be obtained from response headers
                or source URL. Defaults to None.
            - timeout (Optional[int]): seconds to wait for successful upload.
                Defaults to 30.
            - interval (Optional[float]): interval between upload status checks.
                Defaults to 0.3.
            - until_ready (Optional[bool]): should we wait until file is
                available via CDN. Defaults to False.

        Returns:
            ``File`` instance

        Raises:
            ``TimeoutError`` if file wasn't uploaded in time

        """
        ffu = cls.upload_from_url(url, store, filename)
        return ffu.wait(timeout=timeout, interval=interval,
                        until_ready=until_ready)

    class FileFromUrl(object):
        """Contains the logic around an upload from url.

        It expects uploading token, for instance::

            >>> ffu = FileFromUrl(token='a6a2db73-2aaf-4124-b2e7-039aec022e18')
            >>> ffu.info()
            {
                "status': "progress",
                "done": 226038,
                "total": 452076
            }
            >>> ffu.update_info()
            {
                "status": "success",
                "file_id": "63f652fd-3f40-4b54-996c-f17dc7db5bf1",
                "is_stored": false,
                "done": 452076,
                "uuid": "63f652fd-3f40-4b54-996c-f17dc7db5bf1",
                "original_filename": "olympia.jpg",
                "is_image": true,
                "total": 452076,
                "size": 452076
            }
            >>> ffu.get_file()
            <uploadcare.File 63f652fd-3f40-4b54-996c-f17dc7db5bf1>

        But it could be failed::

            >>> ffu.update_info()
            {
                "status": "error",
                "error": "some error message"
            }

        """

        def __init__(self, token):
            self.token = token

            self._info_cache = None

        def __repr__(self):
            return '<uploadcare.File.FileFromUrl {0}>'.format(self.token)

        def info(self):
            """Returns actual information about uploading as ``dict``.

            First time it makes API request to get information and keeps
            it for further using.

            """
            if self._info_cache is None:
                self.update_info()
            return self._info_cache

        def update_info(self):
            """Updates and returns information by requesting Uploadcare API."""
            result = uploading_request('POST', 'from_url/status/',
                                       data={'token': self.token})
            if 'status' not in result:
                raise APIError(
                    'could not find status in result: {0}'.format(result)
                )
            self._info_cache = result
            return result

        def get_file(self):
            """Returns ``File`` instance if upload is completed."""
            if self.info()['status'] == 'success':
                return File(self.info()['uuid'])

        def wait(self, timeout=30, interval=0.3, until_ready=False):

            def check_file():
                status = self.update_info()['status']
                if status == 'success':
                    return self.get_file()
                if status in ('failed', 'error'):
                    raise UploadError(
                        'could not upload file from url: {0}'.format(self.info())
                    )

            time_started = time.time()
            while time.time() - time_started < timeout:
                file = check_file()
                if file and (not until_ready or
                             file.update_info().get('is_ready')):
                    return file
                time.sleep(interval)
            else:
                raise TimeoutError('timed out during upload')


GROUP_ID_REGEX = re.compile('''
    (?P<group_id>
        [a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}
        ~
        (?P<files_qty>\d+)
    )
''', re.VERBOSE)


class FileGroup(object):
    """File Group resource for working with user-uploaded group of files.

    It can take group id or group CDN url::

        >>> file_group = FileGroup('0513dda0-582f-447d-846f-096e5df9e2bb~2')

    You can iterate ``file_group`` or get ``File`` instance by key::

        >>> [file_ for file_ in file_group]
        [<uploadcare.File 6c5e9526-b0fe-4739-8975-72e8d5ee6342>, None]
        >>> file_group[0]
        <uploadcare.File 6c5e9526-b0fe-4739-8975-72e8d5ee6342>
        >>> len(file_group)
        2

    But slicing is not supported because ``FileGroup`` is immutable::

        >>> file_group[:]
        TypeError: slicing is not supported

    If file was deleted then you will get ``None``::

        >>> file_group[1]
        None

    """

    def __init__(self, cdn_url_or_group_id):
        matches = GROUP_ID_REGEX.search(cdn_url_or_group_id)

        if not matches:
            raise InvalidParamError("Couldn't find group id")

        files_qty = int(matches.groupdict()['files_qty'])
        if files_qty <= 0:
            raise InvalidParamError("Couldn't find group id")

        self.id = matches.groupdict()['group_id']

        self._files_qty = files_qty
        self._info_cache = None

    def __repr__(self):
        return '<uploadcare.FileGroup {0}>'.format(self.id)

    def __str__(self):
        return self.cdn_url

    def __len__(self):
        return self._files_qty

    def __getitem__(self, key):
        """Returns file from group by key as ``File`` instance."""
        if isinstance(key, slice):
            raise TypeError('slicing is not supported')
        else:
            file_info = self.info()['files'][key]
            if file_info is not None:
                return File.construct_from(file_info)

    @property
    def _api_uri(self):
        return 'groups/{0}/'.format(self.id)

    @property
    def _api_storage_uri(self):
        return 'groups/{0}/storage/'.format(self.id)

    @property
    def cdn_url(self):
        """Returns group's CDN url.

        Usage example::

            >>> file_group = FileGroup('0513dda0-582f-447d-846f-096e5df9e2bb~2')
            >>> file_group.cdn_url
            https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/

        """
        return '{cdn_base}{group_id}/'.format(
            cdn_base=conf.cdn_base,
            group_id=self.id
        )

    @property
    def file_cdn_urls(self):
        """Returns CDN urls of all files from group without API requesting.

        Usage example::

            >>> file_group = FileGroup('0513dda0-582f-447d-846f-096e5df9e2bb~2')
            >>> file_group.file_cdn_urls[0]
            'https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/nth/0/'

        """
        file_cdn_urls = []
        for file_index in six.moves.xrange(len(self)):
            file_cdn_url = '{group_cdn_url}nth/{file_index}/'.format(
                group_cdn_url=self.cdn_url,
                file_index=file_index
            )
            file_cdn_urls.append(file_cdn_url)
        return file_cdn_urls

    def info(self):
        """Returns all available group information as ``dict``.

        First time it makes API request to get group information and keeps it
        for further using.

        """
        if self._info_cache is None:
            self.update_info()
        return self._info_cache

    def update_info(self):
        """Updates and returns group information by requesting Uploadcare API.
        """
        self._info_cache = rest_request('GET', self._api_uri)
        return self._info_cache

    def datetime_stored(self):
        """Returns file group's store aware *datetime* in UTC format."""
        if self.info().get('datetime_stored'):
            return dateutil.parser.parse(self.info()['datetime_stored'])

    def datetime_created(self):
        """Returns file group's create aware *datetime* in UTC format."""
        if self.info().get('datetime_created'):
            return dateutil.parser.parse(self.info()['datetime_created'])

    def is_stored(self):
        """Returns ``True`` if file is stored.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get('datetime_stored') is not None

    def store(self):
        """Stores all group's files by requesting Uploadcare API.

        Uploaded files do not immediately appear on Uploadcare CDN.

        """
        if self.is_stored():
            return

        self._info_cache = rest_request('PUT', self._api_storage_uri)

    @classmethod
    def construct_from(cls, group_info):
        """Constructs ``FileGroup`` instance from group information."""
        group = cls(group_info['id'])
        group._info_cache = group_info
        return group

    @classmethod
    def create(cls, files):
        """Creates file group and returns ``FileGroup`` instance.

        It expects iterable object that contains ``File`` instances, e.g.::

            >>> file_1 = File('6c5e9526-b0fe-4739-8975-72e8d5ee6342')
            >>> file_2 = File('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> FileGroup.create((file_1, file_2))
            <uploadcare.FileGroup 0513dda0-6666-447d-846f-096e5df9e2bb~2>

        """
        data = {}
        for index, file_ in enumerate(files):
            if isinstance(file_, File):
                file_index = 'files[{index}]'.format(index=index)
                data[file_index] = six.text_type(file_)
            else:
                raise InvalidParamError(
                    'all items have to be ``File`` instance'
                )
        if not data:
            raise InvalidParamError('set of files is empty')

        group_info = uploading_request('POST', 'group/', data=data)

        group = cls.construct_from(group_info)
        return group


def api_iterator(cls, next_url, limit=None):
    while next_url and limit != 0:
        result = rest_request('GET', next_url)
        working_set = result['results']
        next_url = result['next']

        for item in working_set:
            yield cls(item)

            if limit is not None:
                limit -= 1
                if limit == 0:
                    return


class BaseApiList(object):
    # abstract
    base_url = None
    constructor = None
    # ordering fields names which must be handled as datetime
    datetime_ordering_fields = ()

    def __init__(self, starting_point=None, ordering=None, limit=None,
                 request_limit=None):
        self.ordering = ordering
        self.limit = limit
        self.request_limit = request_limit
        self.starting_point = starting_point
        self._count = None

    @property
    def starting_point(self):
        return self._starting_point

    @starting_point.setter
    def starting_point(self, value):
        ordering_field = (self.ordering or '').lstrip('-')
        datetime_fields = self.datetime_ordering_fields

        if value and ordering_field in datetime_fields:
            if not isinstance(value, (datetime, date)):
                raise ValueError('The starting_point must be a datetime')
            value = value.isoformat()

        self._starting_point = value

    def api_url(self, **qs):
        if self.starting_point is not None:
            qs.setdefault('from', self.starting_point)

        if self.ordering is not None:
            qs.setdefault('ordering', self.ordering)

        if self.request_limit:
            qs.setdefault('limit', self.request_limit)

        return self.base_url + '?' + urlencode(qs)

    def __iter__(self):
        return api_iterator(self.constructor, self.api_url(), self.limit)

    def count(self):
        if self.starting_point:
            raise ValueError(
                'Can\'t count objects if the `starting_point` present')
        if self._count is None:
            result = rest_request('GET', self.api_url(limit='1'))
            self._count = result['total']
        return self._count


class FileList(BaseApiList):
    """ List of File resources.

    This class provides iteration over all uploaded files.

    You can specify:

    - ``starting_point`` -- a starting point for filtering files.
      It is reflects a ``from`` parameter from REST API.
    - ``ordering`` -- a string with name of the field what must be used
      for sorting files. The actual list of supported fields you can find in
      documentation: http://uploadcare.com/documentation/rest/#file-files
    - ``limit`` -- a total number of objects to be iterated.
      If not specified, all available objects are iterated;
    - ``request_limit`` -- a number of objects retrieved per request (page).
      Usually, you don't need worry about this parameter.
    - ``stored`` -- ``True`` to include only stored files,
      ``False`` to exclude, ``None`` is default, will not exclude anything;
    - ``removed`` -- ``True`` to include only removed files,
      ``False`` to exclude, ``None`` will not exclude anything.
      The default is ``False``.

    Files can't be stored and removed at the same time, such query will
    always return an empty set.

    But files can be not stored and not removed (just uploaded files).

    Usage example::

        >>> for f in FileList(removed=None):
        >>>     print(f.datetime_uploaded())

    Count objects::

        >>> print('Number of stored files is', FileList(stored=True).count())

    """
    base_url = '/files/'
    constructor = File.construct_from
    datetime_ordering_fields = ('', 'datetime_uploaded')

    def __init__(self, *args, **kwargs):
        self.stored = kwargs.pop('stored', None)
        self.removed = kwargs.pop('removed', None)
        super(FileList, self).__init__(*args, **kwargs)

    def api_url(self, **qs):
        if self.stored is not None:
            qs.setdefault('stored', str(bool(self.stored)).lower())

        if self.removed is not None:
            qs.setdefault('removed', str(bool(self.removed)).lower())

        return super(FileList, self).api_url(**qs)


class FilesStorage(object):
    """ Batch storage operations for the list of files.
    ``store`` and ``delete`` are supported.
    """
    storage_url = '/files/storage/'
    chunk_size = 100

    def __init__(self, seq):
        """ Seq can be:
        * list of UUIDs
        * list of File's instances
        * instance of FileList
        """
        if not isinstance(seq, Iterable):
            raise TypeError('``seq`` must be an iterable')

        self._seq = seq

    def store(self):
        """ Store all specified files.
        """
        return self._base_opration('PUT')

    def delete(self):
        """ Delete all specified files.
        """
        return self._base_opration('DELETE')

    def _base_opration(self, method):
        """ Base method for storage operations.
        """
        uuids = self.uuids()

        while True:
            chunk = list(islice(uuids, 0, self.chunk_size))

            if not chunk:
                return

            rest_request(method, self.storage_url, chunk)

    def uuids(self):
        """ Extract uuid from each item of specified ``seq``.
        """
        for f in self._seq:
            if isinstance(f, File):
                yield f.uuid
            elif isinstance(f, six.string_types):
                yield f
            else:
                raise ValueError(
                    'Invalid type for sequence item: {0}'.format(type(f)))


class GroupList(BaseApiList):
    """List of FileGroup resources.

    This class provides iteration over all groups for project. You can specify:

    - ``starting_point`` -- a starting point for filtering groups.
      It is reflects a ``from`` parameter from the REST API.
    - ``ordering`` -- a string with name of the field what must be used
      for sorting files. The actual list of supported fields you can find in
      documentation: https://uploadcare.com/docs/api_reference/rest/accessing_groups/#properties
    - ``limit`` -- a total number of objects to be iterated.
      If not specified, all available objects are iterated;
    - ``request_limit`` -- a number of objects retrieved per request (page).
      Usually, you don't need worry about this parameter.

    Usage example::

        >>> from datetime import datetime, timedelta
        >>> last_week = datetime.now() - timedelta(weeks=1)
        >>> for f in GroupList(starting_point=last_week):
        >>>     print(f.datetime_created())

    Count objects::

        >>> print('Number of groups is', GroupList().count())

    """
    base_url = '/groups/'
    constructor = FileGroup.construct_from
    datetime_ordering_fields = ('', 'datetime_created')
