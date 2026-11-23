"""Entities of the Project API.

The same models describe both responses and update requests. A request
carries only the fields that were explicitly set (``exclude_unset``). The
server rejects a non-empty feature object for a feature the owner's plan does
not include, so a project fetched from the API can not be sent back as is.

Enum-like response fields are typed as ``str`` so that a value added on the
server later does not break parsing; the enums below list the known values
and can be passed wherever such a field is set.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_serializer

from pyuploadcare.api.entities import Entity
from pyuploadcare.api.responses import PaginatedResponse, Response


# Read-only fields are never sent back to the server.
PROJECT_READ_ONLY_FIELDS: Dict[str, Any] = {
    "pub_key": True,
    "is_shared_project": True,
    "features": {"team_members": True},
}


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


class ProjectFeature(Entity):
    """A feature that can only be switched on and off."""

    is_enabled: Optional[bool] = None


class UploadsFeature(Entity):
    # In bytes, a multiple of a megabyte. `None` means the plan's maximum.
    filesize_limit: Optional[int] = Field(default=None, ge=0)
    autostore: Optional[bool] = None
    # In pixels, a multiple of 10^6. `None` means the default value.
    image_resolution_limit: Optional[int] = Field(
        default=None, ge=1_000_000, le=75_000_000
    )
    is_signed_upload_enabled: Optional[bool] = None


class MimeTypeFilteringFeature(ProjectFeature):
    # Allowed MIME types, from ``ProjectAPIClient.list_mime_types()``.
    mime_types: Optional[List[str]] = None


class UnsafeContentDetectionFeature(ProjectFeature):
    # One of `AutoModeration`.
    auto_moderation: Optional[str] = None


class AdaptiveBitrateStreamingProfile(Entity):
    # `AdaptiveBitrateStreamingResolution` values, 1 to 8 unique items.
    resolutions: List[str] = Field(min_length=1, max_length=8)


class AdaptiveBitrateStreamingProfiles(Entity):
    """Profiles indexed by codec.

    Sending profiles replaces all existing ones, so omit ``h265`` to remove
    the H.265 profile.
    """

    h264: AdaptiveBitrateStreamingProfile
    h265: Optional[AdaptiveBitrateStreamingProfile] = None


class AdaptiveBitrateStreamingFeature(ProjectFeature):
    profiles: Optional[AdaptiveBitrateStreamingProfiles] = None


class TeamMembersFeature(Entity):
    # Read-only. Counts the project owner too.
    team_size: Optional[int] = None


class ProjectFeatures(Entity):
    uploads: Optional[UploadsFeature] = None
    mime_type_filtering: Optional[MimeTypeFilteringFeature] = None
    gif_to_video_conversion: Optional[ProjectFeature] = None
    video_processing: Optional[ProjectFeature] = None
    malware_protection: Optional[ProjectFeature] = None
    svg_validation: Optional[ProjectFeature] = None
    unsafe_content_detection: Optional[UnsafeContentDetectionFeature] = None
    adaptive_bitrate_streaming: Optional[AdaptiveBitrateStreamingFeature] = (
        None
    )
    document_conversion: Optional[ProjectFeature] = None
    exif_metadata_removal: Optional[ProjectFeature] = None
    ai_operations: Optional[ProjectFeature] = None
    team_members: Optional[TeamMembersFeature] = None


class Project(Entity):
    pub_key: Optional[str] = None
    name: Optional[str] = None
    is_blocked: Optional[bool] = None
    is_search_index_allowed: Optional[bool] = None
    is_shared_project: Optional[bool] = None
    features: Optional[ProjectFeatures] = None

    def to_payload(self) -> Dict[str, Any]:
        """The request body: explicitly set, writable fields only."""
        return self.model_dump(
            mode="json",
            exclude_unset=True,
            exclude=PROJECT_READ_ONLY_FIELDS,
        )


class ProjectListResponse(PaginatedResponse):
    results: List[Project]  # type: ignore


class UsageDataPoint(Entity):
    date: date
    value: int


class UsageMetric(Entity):
    metric: str
    unit: str
    data: List[UsageDataPoint]


class CombinedUsageDataPoint(Entity):
    date: date
    traffic: int = 0
    storage: int = 0
    operations: int = 0


class CombinedUsage(Entity):
    # Metric name to its unit, e.g. ``{"traffic": "bytes"}``.
    units: Dict[str, str]
    data: List[CombinedUsageDataPoint]


class ModerationThreshold(Entity):
    category_id: int
    # One of `ModerationFileType`.
    file_type: str = ModerationFileType.IMAGE.value
    # 0 to 100, up to two decimal places.
    threshold_percentage: Decimal = Field(
        ge=0, le=100, max_digits=5, decimal_places=2
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("threshold_percentage")
    def _serialize_threshold(self, value: Decimal) -> str:
        # The API takes the decimal as a string; `str()` keeps it exact.
        return str(value)

    def to_payload(self) -> Dict[str, Any]:
        """The request body item: read-only timestamps are left out."""
        return self.model_dump(
            mode="json",
            include={"category_id", "file_type", "threshold_percentage"},
        )


class ModerationThresholdsResponse(Response):
    thresholds: List[ModerationThreshold]


class ModerationCategory(Entity):
    id: int
    parent_id: Optional[int] = None
    name: str
    # Empty string if the category has no description.
    description: str = ""
    # Depth of the category in the category tree, starting at 1.
    level: int


class ModerationCategoriesResponse(Response):
    categories: List[ModerationCategory]


class MimeTypesResponse(Response):
    mime_types: List[str]
