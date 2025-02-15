from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, PrivateAttr
from typing_extensions import Annotated, Literal, NamedTuple

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
    color_mode: Optional[ColorMode] = None
    orientation: Optional[int] = None
    format: str
    sequence: Optional[bool] = None
    height: int
    width: int
    geo_location: Optional[GEOPoint] = None
    datetime_original: Optional[datetime] = None
    dpi: Optional[Tuple[int, int]] = None


class ImageInfoWithFaces(ImageInfo):
    faces: List[Face]


class AudioStreamInfo(Entity):
    bitrate: Optional[Decimal] = None
    codec: Optional[str] = None
    sample_rate: Optional[Decimal] = None
    profile: Optional[str] = None
    channels: Optional[int] = None


class VideoStreamInfo(Entity):
    height: Decimal
    width: Decimal
    frame_rate: float
    bitrate: Optional[Decimal] = None
    codec: Optional[str] = None


class VideoInfo(Entity):
    duration: Optional[Decimal] = None
    format: str
    bitrate: Optional[Decimal] = None
    audio: List[AudioStreamInfo]
    video: List[VideoStreamInfo]


class MIMEInfo(Entity):
    mime: str
    type: str
    subtype: str


class ContentInfo(Entity):
    mime: Optional[MIMEInfo] = None
    image: Optional[ImageInfo] = None
    video: Optional[VideoInfo] = None


class ApllicationDataDetails(Entity):
    pass


DetailsType = TypeVar(
    "DetailsType", bound=ApllicationDataDetails, covariant=True
)


class ApplicationDataBase(Entity):
    data: Optional[Union[Dict[str, Any], ApllicationDataDetails]] = Field(
        default_factory=lambda: {}
    )
    version: str
    datetime_created: datetime
    datetime_updated: datetime


class AWSRecognitionLabel(Entity):
    confidence: Decimal = Field(alias="Confidence")
    instances: List[Dict] = Field(alias="Instances")
    name: str = Field(alias="Name")
    parents: List[Dict] = Field(alias="Parents")


class AWSRecognitionDetectLabelsDetails(ApllicationDataDetails):
    label_model_version: Optional[str] = Field(None, alias="LabelModelVersion")
    labels: List[AWSRecognitionLabel] = Field(
        alias="Labels", default_factory=list
    )


class AWSRecognitionDetectLabelsApplicationData(ApplicationDataBase):
    data: AWSRecognitionDetectLabelsDetails


class AWSRecognitionModerationLabel(Entity):
    confidence: Decimal = Field(alias="Confidence")
    name: str = Field(alias="Name")
    parent_name: str = Field(alias="ParentName")


class AWSRecognitionDetectModerationLabelsDetails(ApllicationDataDetails):
    label_model_version: Optional[str] = Field(
        None, alias="ModerationModelVersion"
    )
    labels: List[AWSRecognitionModerationLabel] = Field(
        alias="ModerationLabels", default_factory=list
    )


class AWSRecognitionDetectModerationLabelsApplicationData(ApplicationDataBase):
    data: AWSRecognitionDetectModerationLabelsDetails


class RemoveBackgroundDetails(ApllicationDataDetails):
    foreground_type: Optional[str] = None


class RemoveBackgroundApplicationData(ApplicationDataBase):
    data: RemoveBackgroundDetails


class UCClamAVDetails(ApllicationDataDetails):
    infected: Optional[bool] = None
    infected_with: Optional[str] = None


class UCClamAVApplicationData(ApplicationDataBase):
    data: UCClamAVDetails


class ApplicationDataSet(Entity):
    aws_rekognition_detect_labels: Optional[
        AWSRecognitionDetectLabelsApplicationData
    ] = None
    aws_rekognition_detect_moderation_labels: Optional[
        AWSRecognitionDetectModerationLabelsApplicationData
    ] = None
    remove_bg: Optional[RemoveBackgroundApplicationData] = None
    uc_clamav_virus_scan: Optional[UCClamAVApplicationData] = None


MetadataKeyConStrType = Annotated[
    str, Field(pattern=META_KEY_PATTERN, max_length=META_KEY_MAX_LEN)
]

MetadataValueConStrType = Annotated[str, Field(max_length=META_VALUE_MAX_LEN)]

MetadataDict = Dict[MetadataKeyConStrType, MetadataValueConStrType]


class FileInfo(UUIDEntity):
    """
    video_info, image_info and rekognition_info were deprecated in REST API v0.7

    video_info, image_info moved to content_info
    rekognition_info moved to app_data

    """

    datetime_removed: Optional[datetime] = None
    datetime_stored: Optional[datetime] = None
    datetime_uploaded: Optional[datetime] = None
    metadata: Optional[MetadataDict] = None
    is_image: Optional[bool] = None
    is_ready: Optional[bool] = None
    mime_type: Optional[str] = None
    original_file_url: Optional[str] = None
    original_filename: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None
    variations: Optional[Dict[str, UUID]] = None
    source: Optional[str] = None
    content_info: Optional[ContentInfo] = None
    appdata: Optional[ApplicationDataSet] = None


class GroupInfo(Entity):
    id: str
    _fetched: Optional[bool] = PrivateAttr(default=False)
    datetime_created: Optional[datetime] = None
    datetime_stored: Optional[datetime] = None
    files_count: Optional[int] = None
    cdn_url: Optional[str] = None
    url: Optional[str] = None
    files: Optional[List[Optional[FileInfo]]] = None


class ColaboratorInfo(Entity):
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class ProjectInfo(Entity):
    collaborators: Optional[List[ColaboratorInfo]] = None
    name: str
    pub_key: str
    autostore_enabled: Optional[bool] = None


class Webhook(Entity):
    id: int
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    event: Optional[str] = None
    target_url: Optional[str] = None
    project: Optional[int] = None
    is_active: Optional[bool] = None
    signing_secret: Optional[str] = None


class DocumentConvertShortInfo(Entity):
    uuid: UUID


class DocumentConvertInfo(DocumentConvertShortInfo):
    original_source: str
    token: int


class DocumentConvertStatus(Entity):
    status: str
    error: Optional[str] = None
    result: DocumentConvertShortInfo


class DocumentConvertConversionFormat(Entity):
    name: str


class DocumentConvertFormat(Entity):
    name: str
    conversion_formats: List[DocumentConvertConversionFormat]
    converted_groups: Dict[str, str]


class DocumentConvertFormatInfo(Entity):
    error: Optional[str] = None
    format: DocumentConvertFormat


class VideoConvertShortInfo(Entity):
    uuid: UUID
    thumbnails_group_uuid: str


class VideoConvertInfo(VideoConvertShortInfo):
    token: int
    original_source: str


class VideoConvertStatus(Entity):
    status: str
    error: Optional[str] = None
    result: VideoConvertShortInfo
