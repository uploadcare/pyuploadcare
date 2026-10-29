"""Pydantic models for Project API v1.0."""

from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import ConfigDict, Field

from pyuploadcare.api.entities import Entity


class FeatureToggle(Entity):
    is_enabled: Optional[bool] = None


class GifToVideoConversion(FeatureToggle):
    pass


class MimeTypeFiltering(FeatureToggle):
    mime_types: Optional[List[str]] = None


class UploadSettings(FeatureToggle):
    filesize_limit: Optional[int] = None
    autostore: Optional[bool] = None
    image_resolution_limit: Optional[int] = None
    is_signed_upload_enabled: Optional[bool] = None


class UnsafeContentDetection(FeatureToggle):
    auto_moderation: Optional[
        Literal["disabled", "enabled", "remove_files"]
    ] = None


AdaptiveBitrateResolution = Literal[
    "240p",
    "360p",
    "480p",
    "576p",
    "720p",
    "1080p",
    "1440p",
    "2160p",
]


class AdaptiveBitrateStreamingProfile(Entity):
    model_config = ConfigDict(extra="forbid")

    resolutions: List[AdaptiveBitrateResolution]


class AdaptiveBitrateStreamingProfiles(Entity):
    model_config = ConfigDict(extra="forbid")

    h264: AdaptiveBitrateStreamingProfile
    h265: Optional[AdaptiveBitrateStreamingProfile] = None


class AdaptiveBitrateStreaming(Entity):
    is_enabled: Optional[bool] = None
    profiles: Optional[AdaptiveBitrateStreamingProfiles] = None


class AiOperations(FeatureToggle):
    pass


class TeamMembers(Entity):
    team_size: Optional[int] = None


class ProjectFeatures(Entity):
    gif_to_video_conversion: Optional[GifToVideoConversion] = None
    mime_type_filtering: Optional[MimeTypeFiltering] = None
    uploads: Optional[UploadSettings] = None
    video_processing: Optional[FeatureToggle] = None
    malware_protection: Optional[FeatureToggle] = None
    svg_validation: Optional[FeatureToggle] = None
    unsafe_content_detection: Optional[UnsafeContentDetection] = None
    adaptive_bitrate_streaming: Optional[AdaptiveBitrateStreaming] = None
    document_conversion: Optional[FeatureToggle] = None
    exif_metadata_removal: Optional[FeatureToggle] = None
    ai_operations: Optional[AiOperations] = None
    team_members: Optional[TeamMembers] = None


class AccountProject(Entity):
    """Account Project API project. This is not REST ProjectInfo."""

    pub_key: Optional[str] = None
    name: Optional[str] = None
    is_blocked: Optional[bool] = None
    is_search_index_allowed: Optional[bool] = None
    is_shared_project: Optional[bool] = None
    features: Optional[ProjectFeatures] = None


class AccountProjectCreate(AccountProject):
    name: str


class AccountProjectPage(Entity):
    next: Optional[str] = None
    previous: Optional[str] = None
    total: int
    per_page: int
    results: List[AccountProject]


class SecretKey(Entity):
    id: str
    secret: str


class SecretKeyInfo(Entity):
    id: str
    hint: Optional[str] = None
    last_used_at: Optional[datetime] = None


class SecretKeyPage(Entity):
    next: Optional[str] = None
    previous: Optional[str] = None
    total: int
    per_page: int
    results: List[SecretKeyInfo]


class ModerationCategory(Entity):
    id: int
    # Required key; null when the category has no parent.
    parent_id: Optional[int]
    name: str
    description: str
    level: int


class ModerationCategories(Entity):
    categories: List[ModerationCategory]


class ModerationThreshold(Entity):
    category_id: int
    file_type: Literal["image"]
    threshold_percentage: str = Field(
        pattern=r"^(100(\.0{1,2})?|([0-9]|[1-9][0-9])(\.\d{1,2})?)$"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ModerationThresholds(Entity):
    thresholds: List[ModerationThreshold]


class MimeTypes(Entity):
    mime_types: List[str]


class UsagePoint(Entity):
    date: date
    value: int


class UsageMetric(Entity):
    metric: str
    unit: str
    data: List[UsagePoint]


class CombinedUsagePoint(Entity):
    date: date
    traffic: Optional[int] = None
    storage: Optional[int] = None
    operations: Optional[int] = None


class CombinedUsage(Entity):
    units: Dict[str, str]
    data: List[CombinedUsagePoint]


class PartnerAuthorization(Entity):
    redirect_uri: str
