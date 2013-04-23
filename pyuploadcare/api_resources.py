# coding: utf-8
import re
import time
import logging

import requests

from . import conf
from .api import RESTClient, UploadingClient
from .exceptions import (
    TimeoutError, InvalidRequestError, APIError,
)


logger = logging.getLogger("pyuploadcare")

UUID_WITH_EFFECTS_REGEX = re.compile(ur'''
    (?P<uuid>[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12})
    (
        /-/(?P<effects>.*)
    )?
''', re.VERBOSE)


class File(object):

    def __init__(self, cdn_url_or_file_id):
        matches = UUID_WITH_EFFECTS_REGEX.search(cdn_url_or_file_id)

        if not matches:
            raise InvalidRequestError("Couldn't find UUID")

        self.uuid = matches.groupdict()['uuid']
        self.default_effects = matches.groupdict()['effects']

        self._info_cache = None

    def __repr__(self):
        return '<uploadcare.File {uuid}>'.format(uuid=self.uuid)

    def __str__(self):
        return self.cdn_url

    @property
    def _api_uri(self):
        return '/files/{0}/'.format(self.uuid)

    @property
    def _api_storage_uri(self):
        return '/files/{0}/storage/'.format(self.uuid)

    @property
    def cdn_url(self):
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
        if self._info_cache is None:
            self.update_info()
        return self._info_cache

    def update_info(self):
        self._info_cache = RESTClient.make_request('GET', self._api_uri)
        return self._info_cache

    def is_stored(self):
        return (self.info().get('datetime_stored') is not None or
                self.info().get('last_keep_claim') is not None)

    def is_removed(self):
        return (self.info().get('datetime_removed') is not None or
                self.info().get('removed') is not None)

    def filename(self):
        return self.info().get('original_filename')

    def store(self):
        self._info_cache = RESTClient.make_request('PUT', self._api_storage_uri)

    def delete(self):
        self._info_cache = RESTClient.make_request('DELETE', self._api_uri)

    @classmethod
    def construct_from(cls, file_info):
        file_ = cls(file_info['file_id'])
        file_.default_effects = file_info.get('default_effects')
        file_._info_cache = file_info
        return file_

    @classmethod
    def upload(cls, file_obj):
        """Uploads a file and returns ``File`` instance."""
        files = UploadingClient.make_request('POST', '/base/',
                                             files={'file': file_obj})
        file_ = cls(files['file'])
        return file_

    @classmethod
    def upload_from_url(cls, url):
        """Uploads file from given url and returns ``FileFromUrl`` instance.
        """
        result = UploadingClient.make_request('POST', '/from_url/',
                                              data={'source_url': url})
        if 'token' not in result:
            raise APIError(
                'could not find token in result: {0}'.format(result)
            )
        file_from_url = cls.FileFromUrl(result['token'])
        return file_from_url

    class FileFromUrl(object):

        def __init__(self, token):
            self.token = token

            self._info_cache = None

        def __repr__(self):
            return '<uploadcare.File.FileFromUrl {0}>'.format(self.token)

        def info(self):
            if self._info_cache is None:
                self.update_info()
            return self._info_cache

        def update_info(self):
            result = UploadingClient.make_request('POST', '/from_url/status/',
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


GROUP_ID_REGEX = re.compile(ur'''
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
            raise InvalidRequestError("Couldn't find group id")

        files_qty = int(matches.groupdict()['files_qty'])
        if files_qty <= 0:
            raise InvalidRequestError("Couldn't find group id")

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
        return '/groups/{0}/'.format(self.id)

    @property
    def _api_storage_uri(self):
        return '/groups/{0}/storage/'.format(self.id)

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
        for file_index in xrange(self._files_qty):
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
        """Updates group information by requesting Uploadcare API."""
        self._info_cache = RESTClient.make_request('GET', self._api_uri)
        return self._info_cache

    def is_stored(self):
        """Returns ``True`` if group is stored.

        It might do API request once because it depends on ``info()``.

        """
        return self.info()['datetime_stored'] is not None

    def store(self):
        """Stores all group's files by requesting Uploadcare API.

        Uploaded files do not immediately appear on Uploadcare CDN.

        """
        if self.is_stored():
            return

        self._info_cache = RESTClient.make_request('PUT', self._api_storage_uri)
