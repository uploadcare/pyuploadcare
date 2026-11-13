from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, PrivateAttr
from typing_extensions import NamedTuple

from .metadata import META_KEY_MAX_LEN, META_KEY_PATTERN, META_VALUE_MAX_LEN


class Entity(BaseModel): ...


class IDEntity(Entity):
    id: UUID


class UUIDEntity(Entity):
    uuid: UUID


class Patterns(str, Enum):
    DEFAULT = "${default}"
    AUTO_FILENAME = "${auto_filename}"
    EFFECTS = "${effects}"
    FILENAME = "${filename}"
    UUID = "${uuid}"
    EXT = "${ext}"


class ColorMode(str, Enum):
    RGB = "RGB"
    RGBA = "RGBA"
    RGBa = "RGBa"
    RGBX = "RGBX"
    L = "L"
    LA = "LA"
    La = "La"
    P = "P"
    PA = "PA"
    CMYK = "CMYK"
    YCbCr = "YCbCr"
    HSV = "HSV"
    LAB = "LAB"


class GEOPoint(Entity):
    latitude: float
    longitude: float


class Face(NamedTuple):
    x: int
    y: int
    width: int
    height: int


WebhookEvent = Literal[
    "file.uploaded",
    "file.infected",  # it will be deprecated in favor of info_upldated in the future updates
    "file.stored",
    "file.deleted",
    "file.info_updated",
]


class ImageInfo(Entity):
    color_mode: ColorMode | None = None
    orientation: int | None = None
    format: str
    sequence: bool | None = None
    height: int
    width: int
    geo_location: GEOPoint | None = None
    datetime_original: datetime | None = None
    dpi: tuple[int, int] | None = None


class ImageInfoWithFaces(ImageInfo):
    faces: list[Face]


class AudioStreamInfo(Entity):
    bitrate: Decimal | None = None
    codec: str | None = None
    sample_rate: Decimal | None = None
    profile: str | None = None
    channels: int | None = None


class VideoStreamInfo(Entity):
    height: Decimal
    width: Decimal
    frame_rate: float
    bitrate: Decimal | None = None
    codec: str | None = None


class VideoInfo(Entity):
    duration: Decimal | None = None
    format: str
    bitrate: Decimal | None = None
    audio: list[AudioStreamInfo]
    video: list[VideoStreamInfo]


class MIMEInfo(Entity):
    mime: str
    type: str
    subtype: str


class ContentInfo(Entity):
    mime: MIMEInfo | None = None
    image: ImageInfo | None = None
    video: VideoInfo | None = None


class ApllicationDataDetails(Entity):
    pass


DetailsType = TypeVar(
    "DetailsType", bound=ApllicationDataDetails, covariant=True
)


class ApplicationDataBase(Entity):
    data: dict[str, Any] | ApllicationDataDetails | None = Field(
        default_factory=lambda: {}
    )
    version: str
    datetime_created: datetime
    datetime_updated: datetime


class AWSRecognitionLabel(Entity):
    confidence: Decimal = Field(alias="Confidence")
    instances: list[dict] = Field(alias="Instances")
    name: str = Field(alias="Name")
    parents: list[dict] = Field(alias="Parents")


class AWSRecognitionDetectLabelsDetails(ApllicationDataDetails):
    label_model_version: str | None = Field(None, alias="LabelModelVersion")
    labels: list[AWSRecognitionLabel] = Field(
        alias="Labels", default_factory=list
    )


class AWSRecognitionDetectLabelsApplicationData(ApplicationDataBase):
    data: AWSRecognitionDetectLabelsDetails


class AWSRecognitionModerationLabel(Entity):
    confidence: Decimal = Field(alias="Confidence")
    name: str = Field(alias="Name")
    parent_name: str = Field(alias="ParentName")


class AWSRecognitionDetectModerationLabelsDetails(ApllicationDataDetails):
    label_model_version: str | None = Field(
        None, alias="ModerationModelVersion"
    )
    labels: list[AWSRecognitionModerationLabel] = Field(
        alias="ModerationLabels", default_factory=list
    )


class AWSRecognitionDetectModerationLabelsApplicationData(ApplicationDataBase):
    data: AWSRecognitionDetectModerationLabelsDetails


class RemoveBackgroundDetails(ApllicationDataDetails):
    foreground_type: str | None = None


class RemoveBackgroundApplicationData(ApplicationDataBase):
    data: RemoveBackgroundDetails


class UCClamAVDetails(ApllicationDataDetails):
    infected: bool | None = None
    infected_with: str | None = None


class UCClamAVApplicationData(ApplicationDataBase):
    data: UCClamAVDetails


class ApplicationDataSet(Entity):
    aws_rekognition_detect_labels: (
        AWSRecognitionDetectLabelsApplicationData | None
    ) = None
    aws_rekognition_detect_moderation_labels: (
        AWSRecognitionDetectModerationLabelsApplicationData | None
    ) = None
    remove_bg: RemoveBackgroundApplicationData | None = None
    uc_clamav_virus_scan: UCClamAVApplicationData | None = None


MetadataKeyConStrType = Annotated[
    str, Field(pattern=META_KEY_PATTERN, max_length=META_KEY_MAX_LEN)
]

MetadataValueConStrType = Annotated[str, Field(max_length=META_VALUE_MAX_LEN)]

MetadataDict = dict[MetadataKeyConStrType, MetadataValueConStrType]


class FileInfo(UUIDEntity):
    """
    video_info, image_info and rekognition_info were deprecated in REST API v0.7

    video_info, image_info moved to content_info
    rekognition_info moved to app_data

    """

    datetime_removed: datetime | None = None
    datetime_stored: datetime | None = None
    datetime_uploaded: datetime | None = None
    metadata: MetadataDict | None = None
    # `[]` when the file has no tags. `None` when the endpoint does not report
    # tags at all, e.g. upload responses.
    tags: list[str] | None = None
    is_image: bool | None = None
    is_ready: bool | None = None
    mime_type: str | None = None
    original_file_url: str | None = None
    original_filename: str | None = None
    size: int | None = None
    url: str | None = None
    variations: dict[str, UUID] | None = None
    source: str | None = None
    content_info: ContentInfo | None = None
    appdata: ApplicationDataSet | None = None


class SearchHighlight(Entity):
    """Matched tokens wrapped in ``<em>`` tags by the search backend.

    A field is populated only when it matched a full-text condition
    (``query`` or ``phrase``). Without such a condition nothing is
    highlighted: the API may then omit the object altogether, or send it
    empty, in which case every field here is ``None``.

    The values contain user-controlled content (filenames, metadata) plus
    markup added by the server. They are **not** trusted HTML: escape the
    surrounding text before rendering them.
    """

    # OpenAPI: array of string
    original_filename: list[str] | None = None
    # OpenAPI: array of string
    detected_mime_type: list[str] | None = None
    # OpenAPI: object with additionalProperties of type string
    metadata: dict[str, str] | None = None


class FileSearchInfo(FileInfo):
    """A file search result: file info plus the match highlight."""

    highlight: SearchHighlight | None = None


class GroupInfo(Entity):
    id: str
    _fetched: bool | None = PrivateAttr(default=False)
    datetime_created: datetime | None = None
    datetime_stored: datetime | None = None
    files_count: int | None = None
    cdn_url: str | None = None
    url: str | None = None
    files: list[FileInfo | None] | None = None


class ColaboratorInfo(Entity):
    email: EmailStr | None = None
    name: str | None = None


class ProjectInfo(Entity):
    collaborators: list[ColaboratorInfo] | None = None
    name: str
    pub_key: str
    autostore_enabled: bool | None = None


class Webhook(Entity):
    id: int
    created: datetime | None = None
    updated: datetime | None = None
    event: str | None = None
    target_url: str | None = None
    project: int | None = None
    is_active: bool | None = None
    signing_secret: str | None = None


class DocumentConvertShortInfo(Entity):
    uuid: UUID


class DocumentConvertInfo(DocumentConvertShortInfo):
    original_source: str
    token: int


class DocumentConvertStatus(Entity):
    status: str
    error: str | None = None
    result: DocumentConvertShortInfo


class DocumentConvertConversionFormat(Entity):
    name: str


class DocumentConvertFormat(Entity):
    name: str
    conversion_formats: list[DocumentConvertConversionFormat]
    converted_groups: dict[str, str]


class DocumentConvertFormatInfo(Entity):
    error: str | None = None
    format: DocumentConvertFormat


class VideoConvertShortInfo(Entity):
    uuid: UUID
    thumbnails_group_uuid: str


class VideoConvertInfo(VideoConvertShortInfo):
    token: int
    original_source: str


class VideoConvertStatus(Entity):
    status: str
    error: str | None = None
    result: VideoConvertShortInfo
