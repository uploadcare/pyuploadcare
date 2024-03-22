import dataclasses
import logging
import re
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union
from uuid import UUID

from pyuploadcare.api.entities import (
    DocumentConvertFormatInfo,
    DocumentConvertInfo,
    Face,
    VideoConvertInfo,
)
from pyuploadcare.exceptions import (
    InvalidParamError,
    InvalidRequestError,
    TimeoutError,
    UploadError,
)
from pyuploadcare.resources.file_group import FileGroup
from pyuploadcare.transformations.document import (
    DocumentFormat,
    DocumentTransformation,
)
from pyuploadcare.transformations.image import ImageTransformation
from pyuploadcare.transformations.video import VideoTransformation


if TYPE_CHECKING:
    from pyuploadcare.client import Uploadcare


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


class File:
    """File resource for working with user-uploaded files.

    It can take file UUID or group CDN url::

        >>> file_ = uploadcare.file('a771f854-c2cb-408a-8c36-71af77811f3b')
        >>> file_.cdn_url
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/
        >>> print uploadcare.file(
        ...     'https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/')
        https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/

    """

    thumbnails_group_uuid: Optional[str] = None

    _client: "Uploadcare"

    def __init__(self, cdn_url_or_file_id, client: "Uploadcare"):
        if isinstance(cdn_url_or_file_id, UUID):
            cdn_url_or_file_id = str(cdn_url_or_file_id)

        matches = UUID_WITH_EFFECTS_REGEX.search(cdn_url_or_file_id)

        if not matches:
            raise InvalidParamError("Couldn't find UUID")

        self._uuid = matches.groupdict()["uuid"]
        self.default_effects: Optional[str] = matches.groupdict()["effects"]

        self._info_cache: Optional[Dict[str, Any]] = None

        self._client = client

    def __repr__(self):
        return f"<uploadcare.File {self.uuid}>"

    def __str__(self):
        return self.cdn_url

    def set_effects(
        self, effects: Optional[Union[str, ImageTransformation]] = None
    ) -> None:
        effects = str(effects) if effects else ""
        self.default_effects = effects

    def _build_effects(
        self, effects: Optional[Union[str, ImageTransformation]] = None
    ):
        effects = str(effects) if effects else ""
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

    def cdn_path(
        self, effects: Optional[Union[str, ImageTransformation]] = None
    ):
        """Returns CDN path with applied effects.

        Usage example::

            >>> >>> file = File('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> file.cdn_path()
            a771f854-c2cb-408a-8c36-71af77811f3b/
            >>> file.cdn_path('effect/flip/-/effect/mirror/')
            a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/-/effect/mirror/
            >>> image_transforamtion = (
            ...     ImageTransformation()
            ...     .smart_resize(440, 600)
            ...     .quality(ImageQuality.smart)
            ... )
            >>> file.cdn_path(image_transforamtion)
            a771f854-c2cb-408a-8c36-71af77811f3b/-/smart_resize/440x600/-/quality/smart/

        """
        transformation = ImageTransformation(effects)
        path = transformation.path(self.uuid)
        return path

    @property
    def cdn_url(self):
        """Returns file's CDN url.

        Usage example::

            >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> file_.cdn_url
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/

        You can set default effects by string::

            >>> file_.set_effects('effect/flip/-/effect/mirror/')
            >>> file_.cdn_url
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/-/effect/mirror/

        or by image transformation builder::

            >>> file_.set_effects(ImageTransformation().grayscale().flip())
            >>> file_.cdn_url
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/grayscale/-/flip/
        """
        return f"{self._client.cdn_base}{self.cdn_path(self.default_effects)}"

    @property
    def info(self):
        """Returns all available file information as ``dict``.

        First time it makes API request to get file information and keeps it
        for further using.

        """
        if self._info_cache is None:
            self.update_info()
        return self._info_cache

    def update_info(self, include_appdata=False):
        """Updates and returns file information by requesting Uploadcare API."""
        self._info_cache = self._client.files_api.retrieve(
            self.uuid, include_appdata=include_appdata
        ).model_dump()
        return self._info_cache

    @property
    def filename(self):
        """Returns original file name, e.g. ``"olympia.jpg"``.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("original_filename")

    @property
    def datetime_stored(self):
        """Returns file's store aware *datetime* in UTC format.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("datetime_stored")

    @property
    def datetime_removed(self):
        """Returns file's remove aware *datetime* in UTC format.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("datetime_removed")

    @property
    def datetime_uploaded(self):
        """Returns file's upload aware *datetime* in UTC format.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("datetime_uploaded")

    @property
    def is_stored(self):
        """Returns ``True`` if file is stored.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("datetime_stored") is not None

    @property
    def is_removed(self):
        """Returns ``True`` if file is removed.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("datetime_removed") is not None

    @property
    def is_image(self):
        """Returns ``True`` if the file is an image.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("is_image")

    @property
    def is_ready(self):
        """Returns ``True`` if the file is fully uploaded on S3.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("is_ready")

    @property
    def size(self):
        """Returns the file size in bytes.

        It might do API request once because it depends on ``info``.

        """
        return self.info.get("size")

    @property
    def mime_type(self):
        """Returns the file MIME type, e.g. ``"image/png"``.

        It might do API request once because it depends on ``info``.

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
        self._info_cache = self._client.files_api.store(self.uuid).model_dump()

    def create_local_copy(
        self,
        effects: Optional[Union[str, ImageTransformation]] = None,
        store=False,
    ) -> "File":
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
        response = self._client.files_api.local_copy(
            source=self.cdn_path(effects), store=store
        )
        return self._client.file(response.result.uuid)

    def create_remote_copy(
        self,
        target,
        effects: Optional[Union[str, ImageTransformation]] = None,
        make_public=None,
        pattern=None,
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
        response = self._client.files_api.remote_copy(**data)
        return response.result

    def delete(self) -> "None":
        """Deletes file by requesting Uploadcare API."""
        self._info_cache = self._client.files_api.delete(
            self.uuid
        ).model_dump()

    def convert(
        self,
        transformation: Union[VideoTransformation, DocumentTransformation],
        store: Optional[bool] = None,
        save_in_group: bool = False,
    ) -> "File":
        """Convert video or document and return converted file.

        Convert video::

            >>> file = uploadcare.file('740e1b8c-1ad8-4324-b7ec-112c79d8eac2')
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
            - transformation (Union[VideoTransformation, DocumentTransformation]): transformation
                path builder with configured parameters.
                Depending on type video or document conversion will be performed.
            - store (Optional[bool]): Should the file be automatically stored. Defaults to None.
                - False - do not store file
                - True - store file
                - None - use project settings
            - save_in_group (bool): Should pages of a multipage document be stored as a file group.
                Available only for documents. Defaults to False.
        """
        if isinstance(transformation, VideoTransformation):
            if save_in_group:
                raise ValueError(
                    "Multipage conversion is available only for documents."
                )
            return self.convert_video(transformation, store=store)
        elif isinstance(transformation, DocumentTransformation):
            return self.convert_document(
                transformation, store=store, save_in_group=save_in_group
            )

        raise ValueError(f"Unsupported transformation: {transformation}")

    def convert_video(
        self,
        transformation: Union[str, VideoTransformation],
        store: Optional[bool] = None,
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
        transformation = VideoTransformation(transformation)
        path = transformation.path(self.uuid)
        response = self._client.video_convert_api.convert(
            paths=[path], store=store
        )
        if response.problems:
            raise InvalidRequestError(str(response.problems))

        conversion_info: VideoConvertInfo = response.result[0]  # type: ignore
        new_uuid = conversion_info.uuid
        thumbnails_group_uuid = conversion_info.thumbnails_group_uuid
        converted_file = self._client.file(new_uuid)
        converted_file.thumbnails_group_uuid = thumbnails_group_uuid
        return converted_file

    def convert_document(
        self,
        transformation: Union[str, DocumentTransformation],
        store: Optional[bool] = None,
        save_in_group: bool = False,
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
        transformation = DocumentTransformation(transformation)
        path = transformation.path(self.uuid)
        response = self._client.document_convert_api.convert(
            paths=[path],
            store=store,
            save_in_group=save_in_group,
        )
        if response.problems:
            raise InvalidRequestError(str(response.problems))

        conversion_info: DocumentConvertInfo = response.result[0]  # type: ignore
        new_uuid = conversion_info.uuid
        return File(new_uuid, self._client)

    def get_converted_document_group(
        self, format: DocumentFormat
    ) -> FileGroup:
        response: DocumentConvertFormatInfo = (
            self._client.document_convert_api.retrieve(self.uuid)
        )
        group_id = response.format.converted_groups[format]
        return self._client.file_group(group_id)

    def detect_faces(self) -> List[Face]:
        response = self._client.url_api.detect_faces(self.uuid)
        return response.faces


class FileFromUrl:
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

    def __init__(self, token, client: "Uploadcare"):
        self.token = token
        self._client = client

        self._info_cache: Optional[Dict[str, Any]] = None

    def __repr__(self):
        return f"<uploadcare.FileFromUrl {self.token}>"

    @property
    def info(self):
        """Returns actual information about uploading as ``dict``.

        First time it makes API request to get information and keeps
        it for further using.

        """
        if not self._info_cache:
            self.update_info()
        return self._info_cache

    def update_info(self):
        """Updates and returns information by requesting Uploadcare API."""
        result = self._client.upload_api.get_upload_from_url_status(self.token)
        self._info_cache = result
        return result

    def get_file(self):
        """Returns ``File`` instance if upload is completed."""
        if self.info["status"] == "success":
            file_id = self.info["uuid"]
            return self._client.file(file_id)

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
