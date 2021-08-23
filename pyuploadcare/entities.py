from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, PrivateAttr


class Entity(BaseModel):
    pass


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
    dpi: Optional[tuple[int, int]]


class AudioStreamInfo(Entity):
    bitrate: Optional[Decimal]
    codec: Optional[str]
    sample_rate: Optional[Decimal]
    channels: Optional[str]


class VideoStreamInfo(Entity):
    height: Decimal
    width: Decimal
    frame_rate: float
    bitrate: Decimal
    codec: str


class VideoInfo(Entity):
    duration: Decimal
    format: str
    bitrate: Decimal
    audio: Optional[AudioStreamInfo]
    video: VideoStreamInfo


class UUIDEntity(Entity):
    uuid: UUID


class FileInfo(UUIDEntity):
    _fetched: Optional[bool] = PrivateAttr(default=False)
    datetime_removed: Optional[datetime]
    datetime_stored: Optional[datetime]
    datetime_uploaded: Optional[datetime]
    image_info: Optional[ImageInfo]
    is_image: Optional[bool]
    is_ready: Optional[bool]
    mime_type: Optional[str]
    original_file_url: Optional[str]
    original_filename: Optional[str]
    size: Optional[int]
    url: Optional[str]
    variations: Optional[Dict[str, UUID]]
    video_info: Optional[VideoInfo]
    source: Optional[str]
    rekognition_info: Optional[Dict[str, Decimal]]
