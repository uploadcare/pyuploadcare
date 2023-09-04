import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, ConstrainedStr, EmailStr, Field, PrivateAttr

from .metadata import META_KEY_MAX_LEN, META_KEY_PATTERN, META_VALUE_MAX_LEN


class Entity(BaseModel):
    ...


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


class ImageInfo(Entity):
    color_mode: ColorMode
    orientation: Optional[int]
    format: str
    sequence: bool
    height: int
    width: int
    geo_location: Optional[GEOPoint]
    datetime_original: Optional[datetime]
    dpi: Optional[Tuple[int, int]]


class AudioStreamInfo(Entity):
    bitrate: Optional[Decimal]
    codec: Optional[str]
    sample_rate: Optional[Decimal]
    channels: Optional[str]


class VideoStreamInfo(Entity):
    height: Decimal
    width: Decimal
    frame_rate: float
    bitrate: Optional[Decimal]
    codec: Optional[str]


class VideoInfo(Entity):
    duration: Optional[Decimal]
    format: str
    bitrate: Optional[Decimal]
    audio: List[AudioStreamInfo]
    video: List[VideoStreamInfo]


class MIMEInfo(Entity):
    mime: str
    type: str
    subtype: str


class ContentInfo(Entity):
    mime: Optional[MIMEInfo]
    image: Optional[ImageInfo]
    video: Optional[VideoInfo]


class ApllicationDataDetails(Entity):
    pass


DetailsType = TypeVar(
    "DetailsType", bound=ApllicationDataDetails, covariant=True
)


class ApplicationDataBase(Entity):
    data: Optional[Union[Dict[str, Any], ApllicationDataDetails]] = Field(
        default_factory=dict
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
    label_model_version: Optional[str] = Field(alias="LabelModelVersion")
    labels: List[AWSRecognitionLabel] = Field(
        alias="Labels", default_factory=list
    )


class AWSRecognitionDetectLabelsApplicationData(ApplicationDataBase):
    data: AWSRecognitionDetectLabelsDetails


class RemoveBackgroundDetails(ApllicationDataDetails):
    foreground_type: Optional[str]


class RemoveBackgroundApplicationData(ApplicationDataBase):
    data: RemoveBackgroundDetails


class UCClamAVDetails(ApllicationDataDetails):
    infected: Optional[bool]
    infected_with: Optional[str]


class UCClamAVApplicationData(ApplicationDataBase):
    data: UCClamAVDetails


class ApplicationDataSet(Entity):
    aws_rekognition_detect_labels: Optional[
        AWSRecognitionDetectLabelsApplicationData
    ]
    remove_bg: Optional[RemoveBackgroundApplicationData]
    uc_clamav_virus_scan: Optional[UCClamAVApplicationData]


class MetadataKeyConStrType(ConstrainedStr):
    regex = re.compile(META_KEY_PATTERN)
    max_length = META_KEY_MAX_LEN


class MetadataValueConStrType(ConstrainedStr):
    max_length = META_VALUE_MAX_LEN


MetadataDict = Dict[MetadataKeyConStrType, MetadataValueConStrType]


class FileInfo(UUIDEntity):
    """
    video_info, image_info and rekognition_info were deprecated in REST API v0.7

    video_info, image_info moved to content_info
    rekognition_info moved to app_data

    """

    datetime_removed: Optional[datetime]
    datetime_stored: Optional[datetime]
    datetime_uploaded: Optional[datetime]
    metadata: Optional[MetadataDict]
    is_image: Optional[bool]
    is_ready: Optional[bool]
    mime_type: Optional[str]
    original_file_url: Optional[str]
    original_filename: Optional[str]
    size: Optional[int]
    url: Optional[str]
    variations: Optional[Dict[str, UUID]]
    source: Optional[str]
    content_info: Optional[ContentInfo]
    appdata: Optional[ApplicationDataSet]


class GroupInfo(Entity):
    id: str
    _fetched: Optional[bool] = PrivateAttr(default=False)
    datetime_created: Optional[datetime]
    datetime_stored: Optional[datetime]
    files_count: Optional[int]
    cdn_url: Optional[str]
    url: Optional[str]
    files: Optional[List[Optional[FileInfo]]]


class ColaboratorInfo(Entity):
    email: Optional[EmailStr]
    name: Optional[str]


class ProjectInfo(Entity):
    collaborators: Optional[List[ColaboratorInfo]]
    name: str
    pub_key: str
    autostore_enabled: Optional[bool]


class Webhook(Entity):
    id: int
    created: Optional[datetime]
    updated: Optional[datetime]
    event: Optional[str]
    target_url: Optional[str]
    project: Optional[str]
    is_active: Optional[bool]
    signing_secret: Optional[str]


class DocumentConvertShortInfo(Entity):
    uuid: UUID


class DocumentConvertInfo(DocumentConvertShortInfo):
    original_source: str
    token: int


class DocumentConvertStatus(Entity):
    status: str
    error: Optional[str]
    result: DocumentConvertShortInfo


class VideoConvertShortInfo(Entity):
    uuid: UUID
    thumbnails_group_uuid: str


class VideoConvertInfo(VideoConvertShortInfo):
    token: int
    original_source: str


class VideoConvertStatus(Entity):
    status: str
    error: Optional[str]
    result: VideoConvertShortInfo
