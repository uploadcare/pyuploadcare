import re

import dateutil.parser

from pyuploadcare import conf
from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.resources.base import ApiMixin
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


class FileGroup(ApiMixin):
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

        files_qty = int(matches.groupdict()["files_qty"])
        if files_qty <= 0:
            raise InvalidParamError("Couldn't find group id")

        self.id = matches.groupdict()["group_id"]

        self._files_qty = files_qty
        self._info_cache = None

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
                return File.construct_from(file_info)

    @property
    def cdn_url(self):
        """Returns group's CDN url.

        Usage example::

            >>> file_group = FileGroup('0513dda0-582f-447d-846f-096e5df9e2bb~2')
            >>> file_group.cdn_url
            https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/

        """
        return f"{conf.cdn_base}{self.id}/"

    @property
    def file_cdn_urls(self):
        """Returns CDN urls of all files from group without API requesting.

        Usage example::

            >>> file_group = FileGroup('0513dda0-582f-447d-846f-096e5df9e2bb~2')
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
        self._info_cache = self.groups_api.retrieve(self.id).dict()
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

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("datetime_stored") is not None

    def store(self):
        """Stores all group's files by requesting Uploadcare API.

        Uploaded files do not immediately appear on Uploadcare CDN.

        """
        if self.is_stored:
            return

        self._info_cache = self.groups_api.store(self.id)

    @classmethod
    def construct_from(cls, group_info):
        """Constructs ``FileGroup`` instance from group information."""
        group = cls(group_info["id"])
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
        if not files:
            raise InvalidParamError("set of files is empty")

        for file_ in files:
            if not isinstance(file_, File):
                raise InvalidParamError(
                    "all items have to be ``File`` instance"
                )

        file_urls = [str(file_) for file_ in files]
        group_info = cls.upload_api.create_group(
            files=file_urls,
            secure_upload=conf.signed_uploads,
            expire=conf.signed_uploads_ttl,
        )

        group = cls.construct_from(group_info)
        return group
