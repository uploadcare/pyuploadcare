import dataclasses
import logging
import mimetypes
import os
import re
import time
from itertools import islice
from typing import IO, Any, Callable, Dict, Iterable, List, Optional, Union
from uuid import UUID

from pyuploadcare import conf
from pyuploadcare.api.entities import DocumentConvertInfo, VideoConvertInfo
from pyuploadcare.exceptions import (
    InvalidParamError,
    InvalidRequestError,
    TimeoutError,
    UploadError,
)
from pyuploadcare.resources.base import ApiMixin
from pyuploadcare.transformations.document import DocumentTransformation
from pyuploadcare.transformations.video import VideoTransformation


logger = logging.getLogger("pyuploadcare")


RE_UUID = "[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}"
RE_UUID_REGEX = re.compile(f"^{RE_UUID}$")
RE_EFFECTS = "(?:[^/]+/)+"  # -/resize/(200x300/)*
UUID_WITH_EFFECTS_REGEX = re.compile(
    f"""
    /?
    (?P<uuid>{RE_UUID})  # required
    (?:
        /
        (?:-/(?P<effects>{RE_EFFECTS}))?
        ([^/]*)  # filename
    )?
$""",
    re.VERBOSE,
)


@dataclasses.dataclass
class UploadProgress:
    total: int
    done: int


class File(ApiMixin):
    """File resource for working with user-uploaded files.

    It can take file UUID or group CDN url::

        >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
        >>> file_.cdn_url
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/
        >>> print File('https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/')
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/

    """

    # batch size for multiple delete and store requests
    batch_chunk_size = 500

    #  minimum file size for multipart uploads
    multipart_min_file_size = 10485760

    # chunk size for multipart uploads
    multipart_chunk_size = 5 * 1024 * 1024

    thumbnails_group_uuid: Optional[str] = None

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
        return f"<uploadcare.File {self.uuid}>"

    def __str__(self):
        return self.cdn_url

    def _build_effects(self, effects=""):
        if self.default_effects is not None:
            effects = (
                f"{self.default_effects}-/{effects}"
                if effects
                else f"{self.default_effects}"
            )
        return effects

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        match = RE_UUID_REGEX.match(value)

        if not match:
            raise InvalidParamError(f"Invalid UUID: {value}")

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
        return f"{self.uuid}/-/{effects}" if effects else f"{self.uuid}/"

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
        return f"{conf.cdn_base}{self.cdn_path(self.default_effects)}"

    @property
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

    @property
    def filename(self):
        """Returns original file name, e.g. ``"olympia.jpg"``.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("original_filename")

    @property
    def datetime_stored(self):
        """Returns file's store aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("datetime_stored")

    @property
    def datetime_removed(self):
        """Returns file's remove aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("datetime_removed")

    @property
    def datetime_uploaded(self):
        """Returns file's upload aware *datetime* in UTC format.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("datetime_uploaded")

    @property
    def is_stored(self):
        """Returns ``True`` if file is stored.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("datetime_stored") is not None

    @property
    def is_removed(self):
        """Returns ``True`` if file is removed.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("datetime_removed") is not None

    @property
    def is_image(self):
        """Returns ``True`` if the file is an image.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("is_image")

    @property
    def is_ready(self):
        """Returns ``True`` if the file is fully uploaded on S3.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("is_ready")

    @property
    def size(self):
        """Returns the file size in bytes.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("size")

    @property
    def mime_type(self):
        """Returns the file MIME type, e.g. ``"image/png"``.

        It might do API request once because it depends on ``info()``.

        """
        return self.info.get("mime_type")

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
        logger.warning(f"API Warning: {warning}")

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

    @staticmethod
    def _get_file_size(file_object: IO) -> int:
        return os.fstat(file_object.fileno()).st_size

    @classmethod
    def upload(  # noqa: C901
        cls,
        file_handle: Union[IO, str],
        store=None,
        size: Optional[int] = None,
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ) -> "File":
        """Uploads a file and returns ``File`` instance.

        Method can accept file object or URL. Depending of file object size
        direct or multipart upload method will be chosen.

        Upload from url::

            >>> file: File = File.upload("https://shorturl.at/fAX28")

        Upload small file, direct upload is used::

            >>> fh = open('small_file.jpg', 'rb')
            >>> file: File = File.upload(fh)

        Upload big file, multipart upload is used::

            >>> with open('big_file.mp4', 'rb') as fh:
            >>>     file: File = File.upload(fh)

        To track uploading progress you can pass optional callback function::

            >>> def print_progress(info: UploadProgress):
            ...     print(f'{info.done}/{info.total} B')
            >>>
            >>> with open('big_file.mp4', 'rb') as fh:
            ...    file: File = File.upload(fh, callback=print_progress)
            0/11000000 B
            5242880/11000000 B
            10485760/11000000 B
            11000000/11000000 B

        Args:
            - file_handle: file object or url to upload to. If file object
                is passed, ``File.upload_files`` (direct upload) or
                ``File.multipart_upload`` (multipart upload) will be used.
                If file URL is passed, ``File.upload_from_url_sync`` will be
                used for uploading.
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - size (Optional[int]): file size in bytes.
                If not set, it is calculated by ``os.fstat``.
                Used for multipart uploading.
            - callback (Optional[Callable[[UploadProgress], Any]]): Optional callback
                accepting ``UploadProgress`` to track uploading progress.

        Returns:
            ``File`` instance

        """

        # assume url is passed if str
        if isinstance(file_handle, str):
            file_url: str = file_handle
            return cls.upload_from_url_sync(
                file_url,
                store=cls._format_store(store),
                callback=callback,
            )

        file_obj: IO = file_handle

        if size is None:
            size = os.fstat(file_obj.fileno()).st_size

        # use direct upload for files less then multipart_min_file_size
        if size < cls.multipart_min_file_size:
            files = cls.upload_files([file_obj], store=store)
            if not files:
                raise ValueError("Failed to get uploaded file from response")
            file: "File" = files[0]

            if callback:
                callback(UploadProgress(total=size, done=size))

            return file

        file = cls.multipart_upload(
            file_obj, store=store, size=size, callback=callback
        )
        return file

    @staticmethod
    def _format_store(store: Optional[bool]) -> str:
        values_map: Dict[Any, str] = {
            None: "auto",
            True: "1",
            False: "0",
        }

        if store not in values_map:
            store = None

        return values_map[store]

    @classmethod
    def upload_files(
        cls, file_objects: List[IO], store: Optional[bool] = None
    ) -> List["File"]:
        """Upload multiple files using direct upload.

        It support files smaller than 100MB only. If you want to upload larger files,
        use Multipart Uploads.

        Args:
            - file_objects: list of file objects to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings

        Returns:
            ``File`` instance

        """
        files = {
            os.path.basename(file_object.name or "")
            or f"file{index}": file_object
            for index, file_object in enumerate(file_objects)
        }

        response = cls.upload_api.upload(
            files=files,
            store=cls._format_store(store),
            secure_upload=conf.signed_uploads,
            expire=conf.signed_uploads_ttl,
        )
        ucare_files = [cls(response[file_name]) for file_name in files]
        return ucare_files

    @classmethod
    def multipart_upload(  # noqa: C901
        cls,
        file_obj: IO,
        store: Optional[bool] = None,
        size: Optional[int] = None,
        mime_type: Optional[str] = None,
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ) -> "File":
        """Upload file straight to s3 by chunks.

        Multipart Uploads are useful when you are dealing with files larger than 100MB
        or explicitly want to use accelerated uploads.

        Args:
            - file_obj: file object to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - size (Optional[int]): file size in bytes.
                If not set, it is calculated by ``os.fstat``
            - mime_type (Optional[str]): file mime type.
                If not set, it is guessed from filename extension.
            - callback (Optional[Callable[[UploadProgress], Any]]): Optional callback
                accepting ``UploadProgress`` to track uploading progress.

        Returns:
            ``File`` instance

        """
        if size is None:
            size = cls._get_file_size(file_obj)

        if not mime_type:
            mime_type, _encoding = mimetypes.guess_type(file_obj.name)

        if not mime_type:
            mime_type = "application/octet-stream"

        start_response = cls.upload_api.start_multipart_upload(
            file_name=file_obj.name,
            file_size=size,
            content_type=mime_type,
            store=cls._format_store(store),
            secure_upload=conf.signed_uploads,
            expire=conf.signed_uploads_ttl,
        )

        multipart_uuid = start_response["uuid"]

        parts: List[str] = start_response["parts"]

        chunk = file_obj.read(cls.multipart_chunk_size)

        uploaded_size = 0

        while chunk:
            chunk_url = parts.pop(0)
            cls.upload_api.multipart_upload_chunk(chunk_url, chunk)
            uploaded_size += len(chunk)

            if callback:
                callback(UploadProgress(total=size, done=uploaded_size))

            chunk = file_obj.read(cls.multipart_chunk_size)

        file_info: Dict = cls.upload_api.multipart_complete(multipart_uuid)
        return cls.construct_from(file_info)

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
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ) -> "File":
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
            - callback (Optional[Callable[[UploadProgress], Any]]): Optional callback
                accepting ``UploadProgress`` to track uploading progress.

        Returns:
            ``File`` instance

        Raises:
            ``TimeoutError`` if file wasn't uploaded in time

        """
        ffu = cls.upload_from_url(url, store, filename)
        return ffu.wait(
            timeout=timeout,
            interval=interval,
            until_ready=until_ready,
            callback=callback,
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
                    f"Invalid type for sequence item: {type(file_)}"
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

    def convert(
        self,
        transformation: Union[VideoTransformation, DocumentTransformation],
        store: Optional[bool] = None,
    ) -> "File":
        """Convert video or document and return converted file.

        Convert video::

            >>> file = File('740e1b8c-1ad8-4324-b7ec-112c79d8eac2')
            >>> transformation = (
            ...     VideoTransformation()
            ...         .format(Format.mp4)
            ...         .size(width=640,height=480, resize_mode=ResizeMode.add_padding)
            ...         .quality(Quality.lighter)
            ...         .cut(start_time='2:30.535', length='2:20.0')
            ...         .thumbs(10)
            ... )
            >>> converted_file: File = file.convert(transformation)
            >>> converted_file.thumbnails_group_uuid
            e16536ff-7250-4376-81a4-596e3fef37b0~10

        Convert document::

            >>> file = File('740e1b8c-1ad8-4324-b7ec-112c79d8eac2')
            >>> transformation = DocumentTransformation().format(DocumentFormat.pdf)
            >>> converted_file: File = file.convert(transformation)

        Arguments:
            - transformation (Union[VideoTransformation, Documenttransformation]): transformation
                path builder with configured parameters.
                Depending on type video or document conversion will be performed.
            - store (Optional[bool]): Should the file be automatically stored. Defaults to None.
                - False - do not store file
                - True - store file
                - None - use project settings
        """
        if isinstance(transformation, VideoTransformation):
            return self.convert_video(transformation, store=store)
        elif isinstance(transformation, DocumentTransformation):
            return self.convert_document(transformation, store=store)

        raise ValueError(f"Unsupported transformation: {transformation}")

    def convert_video(
        self, transformation: VideoTransformation, store: Optional[bool] = None
    ) -> "File":
        """Convert video and return converted file instance.

        Arguments:
            - transformation (VideoTransformation): transformation path builder
                with configured parameters.
            - store (Optional[bool]): Should the file be automatically stored. Defaults to None.
                - False - do not store file
                - True - store file
                - None - use project settings
        """
        path = transformation.path(self.uuid)
        response = self.video_convert_api.convert(paths=[path], store=store)
        if response.problems:
            raise InvalidRequestError(response.problems)

        conversion_info: VideoConvertInfo = response.result[0]
        new_uuid = conversion_info.uuid
        thumbnails_group_uuid = conversion_info.thumbnails_group_uuid
        converted_file = File(new_uuid)
        converted_file.thumbnails_group_uuid = thumbnails_group_uuid
        return converted_file

    def convert_document(
        self,
        transformation: DocumentTransformation,
        store: Optional[bool] = None,
    ) -> "File":
        """Convert document and return converted file instance.

        Arguments:
            - transformation (DocumentTransformation): transformation path builder
                with configured parameters.
            - store (Optional[bool]): Should the file be automatically stored. Defaults to None.
                - False - do not store file
                - True - store file
                - None - use project settings
        """
        path = transformation.path(self.uuid)
        response = self.document_convert_api.convert(paths=[path], store=store)
        if response.problems:
            raise InvalidRequestError(response.problems)

        conversion_info: DocumentConvertInfo = response.result[0]
        new_uuid = conversion_info.uuid
        return File(new_uuid)


class FileFromUrl(ApiMixin):
    """Contains the logic around an upload from url.

    It expects uploading token, for instance::

        >>> ffu = FileFromUrl(token='a6a2db73-2aaf-4124-b2e7-039aec022e18')
        >>> ffu.info
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
        return f"<uploadcare.FileFromUrl {self.token}>"

    @property
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
        if self.info["status"] == "success":
            return File(self.info["uuid"])

    def wait(  # noqa: C901
        self,
        timeout=30,
        interval=0.3,
        until_ready=False,
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ):
        def check_file():
            info = self.update_info()
            status = info["status"]

            if callback:
                callback(
                    UploadProgress(total=info["total"], done=info["done"])
                )

            if status == "success":
                return self.get_file()
            if status in ("failed", "error"):
                raise UploadError(
                    f"could not upload file from url: {self.info}"
                )

        time_started = time.time()
        while time.time() - time_started < timeout:
            file = check_file()
            if file and (
                not until_ready or file.update_info().get("is_ready")
            ):
                return file
            time.sleep(interval)

        raise TimeoutError("timed out during upload")
