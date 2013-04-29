# coding: utf-8
from __future__ import unicode_literals
import re
import logging

import dateutil.parser
import six

from . import conf
from .api import rest_request, uploading_request
from .exceptions import InvalidRequestError, APIError


logger = logging.getLogger("pyuploadcare")

UUID_WITH_EFFECTS_REGEX = re.compile('''
    (?P<uuid>[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12})
    (
        /-/(?P<effects>.*)
    )?
''', re.VERBOSE)


class File(object):
    """File resource for working with user-uploaded files.

    It can take file UUID or group CDN url::

        >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
        >>> file_.cdn_url
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/
        >>> print File('http://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/')
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/

    """

    def __init__(self, cdn_url_or_file_id):
        matches = UUID_WITH_EFFECTS_REGEX.search(cdn_url_or_file_id)

        if not matches:
            raise InvalidRequestError("couldn't find UUID")

        self.uuid = matches.groupdict()['uuid']
        self.default_effects = matches.groupdict()['effects']

        self._info_cache = None

    def __repr__(self):
        return '<uploadcare.File {uuid}>'.format(uuid=self.uuid)

    def __str__(self):
        return self.cdn_url

    @property
    def _api_uri(self):
        return 'files/{0}/'.format(self.uuid)

    @property
    def _api_storage_uri(self):
        return 'files/{0}/storage/'.format(self.uuid)

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
        if self.default_effects:
            return '{cdn_base}{uuid}/-/{effects}'.format(
                cdn_base=conf.cdn_base,
                uuid=self.uuid,
                effects=self.default_effects
            )
        else:
            return '{cdn_base}{uuid}/'.format(
                cdn_base=conf.cdn_base,
                uuid=self.uuid
            )

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
    def upload(cls, file_obj):
        """Uploads a file and returns ``File`` instance."""
        files = uploading_request('POST', 'base/', files={'file': file_obj})
        file_ = cls(files['file'])
        return file_

    @classmethod
    def upload_from_url(cls, url):
        """Uploads file from given url and returns ``FileFromUrl`` instance.
        """
        result = uploading_request('POST', 'from_url/',
                                   data={'source_url': url})
        if 'token' not in result:
            raise APIError(
                'could not find token in result: {0}'.format(result)
            )
        file_from_url = cls.FileFromUrl(result['token'])
        return file_from_url

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
            raise InvalidRequestError("couldn't find group id")

        files_qty = int(matches.groupdict()['files_qty'])
        if files_qty <= 0:
            raise InvalidRequestError("couldn't find group id")

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
                data[file_index] = six.u(str(file_))
            else:
                raise InvalidRequestError(
                    'all items have to be ``File`` instance'
                )
        if not data:
            raise InvalidRequestError('set of files is empty')

        group_info = uploading_request('POST', 'group/', data=data)

        group = cls.construct_from(group_info)
        return group
