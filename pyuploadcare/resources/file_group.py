import re
import warnings
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, Optional

import dateutil.parser

from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.resources.utils import (
    coerce_to_optional_datetime,
    max_for_optional_datetimes,
)


if TYPE_CHECKING:
    from pyuploadcare.client import Uploadcare
    from pyuploadcare.resources.file import File


GROUP_ID_REGEX = re.compile(
    r"""
    (?P<group_id>
        [a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}
        ~
        (?P<files_qty>\d+)
    )
""",
    re.VERBOSE,
)


class FileGroup(Iterable):
    """File Group resource for working with user-uploaded group of files.

    It can take group id or group CDN url::

        >>> file_group = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')

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

    def __init__(self, cdn_url_or_group_id: str, client: "Uploadcare"):
        matches = GROUP_ID_REGEX.search(cdn_url_or_group_id)

        if not matches:
            raise InvalidParamError("Couldn't find group id")

        files_qty = int(matches.groupdict()["files_qty"])
        if files_qty <= 0:
            raise InvalidParamError("Couldn't find group id")

        self.id = matches.groupdict()["group_id"]

        self._is_deleted = False
        self._stored_at: Optional[datetime] = None
        self._files_qty = files_qty
        self._info_cache: Optional[Dict[str, Any]] = None

        self._client = client

    def __repr__(self):
        return f"<uploadcare.FileGroup {self.id}>"

    def __str__(self):
        return self.cdn_url

    def __len__(self):
        return self._files_qty

    def __getitem__(self, key):
        """Returns file from group by key as ``File`` instance."""
        if isinstance(key, slice):
            raise TypeError("slicing is not supported")
        else:
            file_info = self.info["files"][key]
            if file_info is not None:
                return self._client.file(file_info["uuid"], file_info)

    def __iter__(self) -> Iterator["File"]:
        for i in range(len(self)):
            file_ = self[i]
            if file_:
                yield file_

    @property
    def cdn_url(self):
        """Returns group's CDN url.

        Usage example::

            >>> file_group = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
            >>> file_group.cdn_url
            https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/

        """
        return f"{self._client.cdn_base}{self.id}/"

    @property
    def file_cdn_urls(self):
        """Returns CDN urls of all files from group without API requesting.

        Usage example::

            >>> file_group = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
            >>> file_group.file_cdn_urls[0]
            'https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/nth/0/'

        """
        file_cdn_urls = []
        for file_index in range(len(self)):
            file_cdn_url = f"{self.cdn_url}nth/{file_index}/"
            file_cdn_urls.append(file_cdn_url)
        return file_cdn_urls

    @property
    def info(self):
        """Returns all available group information as ``dict``.

        First time it makes API request to get group information and keeps it
        for further using.

        """
        if self._info_cache is None:
            self.update_info()
        return self._info_cache

    def update_info(self):
        """Updates and returns group information by requesting Uploadcare API."""
        self._info_cache = self._client.groups_api.retrieve(
            self.id
        ).model_dump()
        if self.is_stored and self._stored_at:
            assert self._info_cache
            self._info_cache["datetime_stored"] = self._stored_at.isoformat()

        return self._info_cache

    @property
    def datetime_stored(self):
        """Returns file group's store aware *datetime* in UTC format."""
        warnings.warn(
            "datetime_stored has been removed from REST API v0.7",
            DeprecationWarning,
        )
        datetime_ = self.info.get("datetime_stored")
        if isinstance(datetime_, str):
            return dateutil.parser.parse(datetime_)

    @property
    def datetime_created(self):
        """Returns file group's create aware *datetime* in UTC format."""
        datetime_ = self.info.get("datetime_created")
        if isinstance(datetime_, str):
            return dateutil.parser.parse(datetime_)

    @property
    def is_stored(self):
        """Returns ``True`` if group is stored.

        It might do several API request
        because it iterates over all files gathered in group.

        """
        is_stored = False
        most_fresh_date: Optional[datetime] = None

        for _file in self:
            if not _file:
                """Due to type of source as Optional[List[Optional[FileInfo]]]"""
                continue

            if not _file.is_stored:
                most_fresh_date = None
                break

            most_fresh_date = max_for_optional_datetimes(
                most_fresh_date,
                coerce_to_optional_datetime(_file.datetime_stored),
            )
        else:
            is_stored = True

        self._stored_at = most_fresh_date
        return is_stored

    def store(self):
        """Stores all group's files by requesting Uploadcare API.

        Uploaded files do not immediately appear on Uploadcare CDN.

        Since pyuploadcare v.4.0. started to use REST API v.0.7
        this method performs multiple API calls
        using batch method for file storing
        and API call for updating collection of files belonging to the group

        """
        if self.is_stored:
            return

        self._client.store_files(file_ for file_ in self)
        self.update_info()
        return self.is_stored

    @property
    def is_deleted(self):
        """Returns ``True`` if group is deleted.

        It makes no API call

        """
        return self._is_deleted

    def delete(self, delete_files: bool = False):
        """Delete group itself, left files unchanged

        Added in API v. 0.7.0

        Args:
            - ``delete_files`` -- ``True`` do also delete files in this group.
        """
        if self._is_deleted:
            return

        if delete_files:
            self._client.delete_files(file_ for file_ in self)

        self._client.groups_api.delete(self.id)
        self._is_deleted = True
