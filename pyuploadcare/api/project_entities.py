"""Entities of the Project API.

The same models describe both responses and update requests. A request
carries only the fields that were explicitly set (``exclude_unset``). The
server rejects a non-empty feature object for a feature the owner's plan does
not include, so a project fetched from the API can not be sent back as is.

Enum-like response fields are typed as ``str`` so that a value added on the
server later does not break parsing; the enums below list the known values
and can be passed wherever such a field is set.

Models that make up a request reject unknown fields on construction, so a
misspelled setting raises an error instead of being dropped. Responses are
parsed with unknown fields ignored (``AccountProjectAPIBase._parse_response``), so
a field added on the server later does not break parsing.

Upload limits keep the API's field names, so the models' JSON schemas match
the API's, but hold the values in megabytes and megapixels. Only the HTTP
boundary uses bytes and pixels: responses are parsed and request bodies are
dumped with the ``API_UNITS`` context, which converts them.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import (
    ConfigDict,
    Field,
    FieldSerializationInfo,
    ValidationInfo,
    field_serializer,
    field_validator,
)

from pyuploadcare.api.entities import Entity
from pyuploadcare.api.responses import PaginatedResponse, Response


# A decimal megabyte (and megapixel), as on the server.
MEGA = 10**6

# Validation and serialization context of the HTTP boundary: upload limits
# are in bytes and pixels there, as the API takes them.
API_UNITS: dict[str, Any] = {"api_units": True}


def _in_api_units(info: ValidationInfo | FieldSerializationInfo) -> bool:
    return bool(info.context and info.context.get("api_units"))


# Read-only fields are never sent back to the server.
PROJECT_READ_ONLY_FIELDS: dict[str, Any] = {
    "pub_key": True,
    "is_shared_project": True,
    "features": {"team_members": True},
}


class RequestEntity(Entity):
    """A model that is also sent to the server: unknown fields are an error."""

    model_config = ConfigDict(extra="forbid")


class UsageMetricName(str, Enum):
    TRAFFIC = "traffic"
    STORAGE = "storage"
    OPERATIONS = "operations"


class AutoModeration(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    REMOVE_FILES = "remove_files"


class AdaptiveBitrateStreamingResolution(str, Enum):
    R240P = "240p"
    R360P = "360p"
    R480P = "480p"
    R576P = "576p"
    R720P = "720p"
    R1080P = "1080p"
    R1440P = "1440p"
    R2160P = "2160p"


class ModerationFileType(str, Enum):
    IMAGE = "image"


class ProjectFeature(RequestEntity):
    """A feature that can only be switched on and off."""

    is_enabled: bool | None = None


class UploadsFeature(RequestEntity):
    """Upload settings.

    The fields are named as in the API, but the limits are in megabytes
    (10^6 bytes) and megapixels, where the API takes bytes and pixels. The
    conversion happens only with the ``API_UNITS`` context.
    """

    # In megabytes. `None` means the plan's maximum.
    filesize_limit: int | None = Field(default=None, ge=0, strict=True)
    autostore: bool | None = None
    # In megapixels. `None` means the default value, 75 megapixels.
    image_resolution_limit: int | None = Field(default=None, ge=0, le=75, strict=True)
    is_signed_upload_enabled: bool | None = None

    @field_validator("filesize_limit", "image_resolution_limit", mode="before")
    @classmethod
    def _from_api_units(cls, value: Any, info: ValidationInfo) -> Any:
        # Rounds down, as the server does when it stores the limit.
        is_int = isinstance(value, int) and not isinstance(value, bool)
        if is_int and _in_api_units(info):
            return value // MEGA
        return value

    @field_serializer("filesize_limit", "image_resolution_limit")
    def _to_api_units(
        self, value: int | None, info: FieldSerializationInfo
    ) -> int | None:
        if value is not None and _in_api_units(info):
            return value * MEGA
        return value


class MimeTypeFilteringFeature(ProjectFeature):
    # Allowed MIME types, from ``AccountProjectAPIClient.list_mime_types()``.
    mime_types: list[str] | None = None


class UnsafeContentDetectionFeature(ProjectFeature):
    # One of `AutoModeration`.
    auto_moderation: str | None = None


class AdaptiveBitrateStreamingProfile(RequestEntity):
    # `AdaptiveBitrateStreamingResolution` values, 1 to 8 unique items.
    resolutions: list[str] = Field(min_length=1, max_length=8)


class AdaptiveBitrateStreamingProfiles(RequestEntity):
    """Profiles indexed by codec.

    Sending profiles replaces all existing ones, so omit ``h265`` to remove
    the H.265 profile.
    """

    h264: AdaptiveBitrateStreamingProfile
    h265: AdaptiveBitrateStreamingProfile | None = None


class AdaptiveBitrateStreamingFeature(ProjectFeature):
    profiles: AdaptiveBitrateStreamingProfiles | None = None


class TeamMembersFeature(RequestEntity):
    # Read-only. Counts the project owner too.
    team_size: int | None = None


class ProjectFeatures(RequestEntity):
    uploads: UploadsFeature | None = None
    mime_type_filtering: MimeTypeFilteringFeature | None = None
    gif_to_video_conversion: ProjectFeature | None = None
    video_processing: ProjectFeature | None = None
    malware_protection: ProjectFeature | None = None
    svg_validation: ProjectFeature | None = None
    unsafe_content_detection: UnsafeContentDetectionFeature | None = None
    adaptive_bitrate_streaming: AdaptiveBitrateStreamingFeature | None = None
    document_conversion: ProjectFeature | None = None
    exif_metadata_removal: ProjectFeature | None = None
    ai_operations: ProjectFeature | None = None
    team_members: TeamMembersFeature | None = None


class Project(RequestEntity):
    pub_key: str | None = None
    name: str | None = None
    is_blocked: bool | None = None
    is_search_index_allowed: bool | None = None
    is_shared_project: bool | None = None
    features: ProjectFeatures | None = None

    def to_payload(self) -> dict[str, Any]:
        """The request body: explicitly set, writable fields in API units."""
        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=True,
            exclude=PROJECT_READ_ONLY_FIELDS,
            context=API_UNITS,
        )


class ProjectListResponse(PaginatedResponse):
    results: list[Project]  # type: ignore


class UsageDataPoint(Entity):
    date: date
    value: int


class UsageMetric(Entity):
    metric: str
    unit: str
    data: list[UsageDataPoint]


class CombinedUsageDataPoint(Entity):
    date: date
    traffic: int = 0
    storage: int = 0
    operations: int = 0


class CombinedUsage(Entity):
    # Metric name to its unit, e.g. ``{"traffic": "bytes"}``.
    units: dict[str, str]
    data: list[CombinedUsageDataPoint]


class ModerationThreshold(RequestEntity):
    category_id: int
    # One of `ModerationFileType`.
    file_type: str = ModerationFileType.IMAGE.value
    # 0 to 100, up to two decimal places.
    threshold_percentage: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_serializer("threshold_percentage")
    def _serialize_threshold(self, value: Decimal) -> str:
        # The API takes the decimal as a string; `str()` keeps it exact.
        return str(value)

    def to_payload(self) -> dict[str, Any]:
        """The request body item: read-only timestamps are left out."""
        return self.model_dump(
            mode="json",
            include={"category_id", "file_type", "threshold_percentage"},
        )


class ModerationThresholdsResponse(Response):
    thresholds: list[ModerationThreshold]


class ModerationCategory(Entity):
    id: int
    parent_id: int | None = None
    name: str
    # Empty string if the category has no description.
    description: str = ""
    # Depth of the category in the category tree, starting at 1.
    level: int


class ModerationCategoriesResponse(Response):
    categories: list[ModerationCategory]


class MimeTypesResponse(Response):
    mime_types: list[str]
