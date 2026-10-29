from enum import Enum
from typing import Any, Dict, Literal, Optional, TypeVar, Union
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from pyuploadcare.api.entities import Entity


class AddonLabels(str, Enum):
    AWS_LABEL_RECOGNITION = "aws_rekognition_detect_labels"
    AWS_MODERATION_LABELS = "aws_rekognition_detect_moderation_labels"
    CLAM_AV = "uc_clamav_virus_scan"
    REMOVE_BG = "remove_bg"


class AddonExecutionParams(Entity):
    pass


AddonParamsType = TypeVar("AddonParamsType", bound=AddonExecutionParams)


class AddonExecutionGeneralRequestData(Entity):
    target: Union[UUID, str]
    params: Optional[Union[Dict[str, Any], AddonExecutionParams]] = None

    @field_validator("target")
    @classmethod
    def coerce_target_to_str(cls, v):
        return str(v)


class AddonClamAVExecutionParams(AddonExecutionParams):
    purge_infected: bool


class AddonClamAVExecutionRequestData(AddonExecutionGeneralRequestData):
    params: Optional[AddonClamAVExecutionParams]


class AddonRemoveBGExecutionParams(AddonExecutionParams):
    model_config = ConfigDict(extra="forbid")

    crop: Optional[bool] = Field(
        None,
        description=(
            "Whether to crop off all empty regions. "
            "Defaults to false when omitted."
        ),
    )
    bg_color: Optional[str] = Field(
        None,
        pattern=r"^[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
        description=(
            "Hex color without a leading #, for example 81d4fa or "
            "81d4fa77. Fills the removed background."
        ),
    )
    channels: Optional[Literal["rgba", "alpha"]] = Field(
        None,
        description=(
            "Finalized image as rgba (the default) or an alpha mask."
        ),
    )


class AddonRemoveBGExecutionRequestData(AddonExecutionGeneralRequestData):
    params: Optional[AddonRemoveBGExecutionParams]
