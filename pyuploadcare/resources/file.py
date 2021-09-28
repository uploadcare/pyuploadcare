import logging
import re
import time
from itertools import islice
from typing import Iterable, List, Union
from uuid import UUID

from pyuploadcare import conf
from pyuploadcare.exceptions import (
    InvalidParamError,
    TimeoutError,
    UploadError,
)
from pyuploadcare.resources.base import ApiMixin


logger = logging.getLogger("pyuploadcare")


RE_UUID = "[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}"
RE_UUID_REGEX = re.compile("^{0}$".format(RE_UUID))
RE_EFFECTS = "(?:[^/]+/)+"  # -/resize/(200x300/)*
UUID_WITH_EFFECTS_REGEX = re.compile(
    """
    /?
    (?P<uuid>{uuid})  # required
    (?:
        /
        (?:-/(?P<effects>{effects}))?
        ([^/]*)  # filename
    )?
$""".format(
        uuid=RE_UUID, effects=RE_EFFECTS
    ),
    re.VERBOSE,
)


class File(ApiMixin):
    """File resource for working with user-uploaded files.

    It can take file UUID or group CDN url::

        >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
        >>> file_.cdn_url
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/
        >>> print File('https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/')
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/

    """

    batch_chunk_size = 500

    def __init__(self, cdn_url_or_file_id):
        if isinstance(cdn_url_or_file_id, UUID):
            cdn_url_or_file_id = str(cdn_url_or_file_id)

        matches = UUID_WITH_EFFECTS_REGEX.search(cdn_url_or_file_id)

        if not matches:
            raise InvalidParamError("Couldn't find UUID")

        self._uuid = matches.groupdict()["uuid"]
        self.default_effects = matches.groupdict()["effects"]

        self._info_cache = None

    def __repr__(self):
        return "<uploadcare.File {uuid}>".format(uuid=self.uuid)

    def __str__(self):
        return self.cdn_url

    def _build_effects(self, effects=""):
        if self.default_effects is not None:
            fmt = "{head}-/{tail}" if effects else "{head}"
            effects = fmt.format(head=self.default_effects, tail=effects)
        return effects

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        match = RE_UUID_REGEX.match(value)

        if not match:
            raise InvalidParamError("Invalid UUID: {0}".format(value))

        self._uuid = match.group(0)

    def cdn_path(self, effects=None):
        """Returns CDN path with applied effects.

        Usage example::

            >>> >>> file = File('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> file.cdn_path()
            a771f854-c2cb-408a-8c36-71af77811f3b/
            >>> file.cdn_path('effect/flip/-/effect/mirror/')
            a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/-/effect/mirror/

        """
        ptn = "{uuid}/-/{effects}" if effects else "{uuid}/"
        return ptn.format(uuid=self.uuid, effects=effects)

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
        return "{cdn_base}{path}".format(
            cdn_base=conf.cdn_base, path=self.cdn_path(self.default_effects)
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
        """Updates and returns file information by requesting Uploadcare API."""
        self._info_cache = self.files_api.retrieve(self.uuid).dict()
        return self._info_cache

    def filename(self):
        """Returns original file name, e.g. ``"olympia.jpg"``.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("original_filename")

    def datetime_stored(self):
        """Returns file's store aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("datetime_stored")

    def datetime_removed(self):
        """Returns file's remove aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("datetime_removed")

    def datetime_uploaded(self):
        """Returns file's upload aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("datetime_uploaded")

    def is_stored(self):
        """Returns ``True`` if file is stored.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("datetime_stored") is not None

    def is_removed(self):
        """Returns ``True`` if file is removed.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("datetime_removed") is not None

    def is_image(self):
        """Returns ``True`` if the file is an image.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("is_image")

    def is_ready(self):
        """Returns ``True`` if the file is fully uploaded on S3.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("is_ready")

    def size(self):
        """Returns the file size in bytes.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("size")

    def mime_type(self):
        """Returns the file MIME type, e.g. ``"image/png"``.

        It might do API request once because it depends on ``info()``.

        """
        return self.info().get("mime_type")

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
        self._info_cache = self.files_api.store(self.uuid).dict()

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
        logger.warn("API Warning: {0}".format(warning))

        if target is not None:
            return self.create_remote_copy(target, effects)
        else:
            return self.create_local_copy(effects)

    def create_local_copy(self, effects=None, store=False) -> "File":
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
        response = self.files_api.local_copy(
            source=self.cdn_path(effects), store=store
        )
        return File(response.result.uuid)

    def create_remote_copy(
        self, target, effects=None, make_public=None, pattern=None
    ) -> str:
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
        data = {"source": self.cdn_path(effects), "target": target}

        if make_public is not None:
            data["make_public"] = make_public
        if pattern is not None:
            data["pattern"] = pattern
        response = self.files_api.remote_copy(**data)
        return response.result

    def delete(self):
        """Deletes file by requesting Uploadcare API."""
        self._info_cache = self.files_api.delete(self.uuid).dict()

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
        file_ = cls(str(file_info["uuid"]))
        file_.default_effects = file_info.get("default_effects")
        file_._info_cache = file_info
        return file_

    @classmethod
    def upload(
        cls,
        file_obj,
        store=None,
    ):
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
            store = "auto"
        elif store:
            store = "1"
        else:
            store = "0"

        response = cls.upload_api.upload(
            files={"file": file_obj},
            store=store,
            secure_upload=conf.signed_uploads,
            expire=conf.signed_uploads_ttl,
        )
        file_ = cls(response["file"])
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
            store = "auto"
        elif store:
            store = "1"
        else:
            store = "0"

        token = cls.upload_api.upload_from_url(
            source_url=url,
            store=store,
            filename=filename,
            secure_upload=conf.signed_uploads,
            expire=conf.signed_uploads_ttl,
        )
        file_from_url = FileFromUrl(token)
        return file_from_url

    @classmethod
    def upload_from_url_sync(
        cls,
        url,
        timeout=30,
        interval=0.3,
        until_ready=False,
        store=None,
        filename=None,
    ):
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
        return ffu.wait(
            timeout=timeout, interval=interval, until_ready=until_ready
        )

    @staticmethod
    def _extracts_uuids(files: Iterable[Union[str, "File"]]) -> List[str]:
        uuids: List[str] = []

        for file_ in files:
            if isinstance(file_, File):
                uuids.append(file_.uuid)
            elif isinstance(file_, str):
                uuids.append(file_)
            else:
                raise ValueError(
                    "Invalid type for sequence item: {0}".format(type(file_))
                )

        return uuids

    @classmethod
    def batch_store(cls, files: Iterable[Union[str, "File"]]):
        """Stores multiple files by requesting Uploadcare API.

        Usage example::

            >>> files = [
            ... '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
            ... 'a771f854-c2cb-408a-8c36-71af77811f3b'
            ... ]
            >>> File.batch_store(files)

        Args:
            - files:
                List of file UUIDs, CND urls or ``File`` instances.
        """
        uuids = cls._extracts_uuids(files)
        start = 0
        chunk = list(islice(uuids, start, cls.batch_chunk_size))
        while chunk:
            cls.files_api.batch_store(uuids)
            start += cls.batch_chunk_size
            chunk = list(islice(uuids, start, cls.batch_chunk_size))

    @classmethod
    def batch_delete(cls, files: Iterable[Union[str, "File"]]):
        """Deletes multiple files by requesting Uploadcare API.

        Usage example::

            >>> files = [
            ... '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
            ... 'a771f854-c2cb-408a-8c36-71af77811f3b'
            ... ]
            >>> File.batch_delete(files)

        Args:
            - files:
                List of file UUIDs, CND urls or ``File`` instances.
        """
        uuids = cls._extracts_uuids(files)
        start = 0
        chunk = list(islice(uuids, start, cls.batch_chunk_size))
        while chunk:
            cls.files_api.batch_delete(uuids)
            start += cls.batch_chunk_size
            chunk = list(islice(uuids, start, cls.batch_chunk_size))


class FileFromUrl(ApiMixin):
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
        return "<uploadcare.File.FileFromUrl {0}>".format(self.token)

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
        result = self.upload_api.get_upload_from_url_status(self.token)
        self._info_cache = result
        return result

    def get_file(self):
        """Returns ``File`` instance if upload is completed."""
        if self.info()["status"] == "success":
            return File(self.info()["uuid"])

    def wait(self, timeout=30, interval=0.3, until_ready=False):  # noqa: C901
        def check_file():
            status = self.update_info()["status"]
            if status == "success":
                return self.get_file()
            if status in ("failed", "error"):
                raise UploadError(
                    "could not upload file from url: {0}".format(self.info())
                )

        time_started = time.time()
        while time.time() - time_started < timeout:
            file = check_file()
            if file and (
                not until_ready or file.update_info().get("is_ready")
            ):
                return file
            time.sleep(interval)
        else:
            raise TimeoutError("timed out during upload")
