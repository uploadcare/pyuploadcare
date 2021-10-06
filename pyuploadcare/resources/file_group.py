import re
from typing import TYPE_CHECKING, Any, Dict, Optional

import dateutil.parser

from pyuploadcare.exceptions import InvalidParamError


if TYPE_CHECKING:
    from pyuploadcare.client import Uploadcare


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


class FileGroup:
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
        self._info_cache = self._client.groups_api.retrieve(self.id).dict()
        return self._info_cache

    @property
    def datetime_stored(self):
        """Returns file group's store aware *datetime* in UTC format."""
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
        """Returns ``True`` if file is stored.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("datetime_stored") is not None

    def store(self):
        """Stores all group's files by requesting Uploadcare API.

        Uploaded files do not immediately appear on Uploadcare CDN.

        """
        if self.is_stored:
            return

        self._info_cache = self._client.groups_api.store(self.id)
