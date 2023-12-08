from enum import Enum
from typing import Any, Dict, Optional, TypeVar, Union
from uuid import UUID

from pydantic import Field, field_validator

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
    crop: Optional[bool] = Field(
        None, description="Whether to crop off all empty regions"
    )
    crop_margin: Optional[str] = Field(
        None,
        description="Adds a margin around the cropped subject, e.g 30px or 30%",
    )
    scale: Optional[str] = Field(
        None,
        description="Scales the subject relative to the total image size, e.g 80%",
    )
    add_shadow: Optional[bool] = Field(
        None, description="Whether to add an artificial shadow to the result"
    )
    type_level: Optional[str] = Field(
        None,
        description="""Enum: "none" "1" "2" "latest"
    "none" = No classification (foreground_type won't bet set in the application data)
    "1" = Use coarse classification classes: [person, product, animal, car, other]
    "2" = Use more specific classification classes:
     [person, product, animal, car, car_interior, car_part, transportation, graphics, other]
    "latest" = Always use the latest classification classes available
    """,
    )
    type: Optional[str] = Field(
        None,
        description="""Foreground type. Enum: "auto" "person" "product" "car""",
    )
    semitransparency: Optional[bool] = Field(
        None,
        description="Whether to have semi-transparent regions in the result",
    )
    channels: Optional[str] = Field(None, description="Enum: 'rgba' 'alpha'")
    roi: Optional[str] = Field(
        None,
        description="""
        Region of interest:
            Only contents of this rectangular region can be detected as foreground.
            Everything outside is considered background and will be removed.
            The rectangle is defined as two x/y coordinates in the format "x1 y1 x2 y2".
            The coordinates can be in absolute pixels (suffix 'px')
            or relative to the width/height of the image (suffix '%').
            By default, the whole image is the region of interest ("0% 0% 100% 100%").
        """,
    )
    position: Optional[str] = Field(
        None,
        description="""
        Positions the subject within the image canvas.
        Can be
           - "original" (default unless "scale" is given),
           - "center" (default when "scale" is given)
           - or a value from "0%" to "100%" (both horizontal and vertical)
           - or two values (horizontal, vertical).
        """,
    )


class AddonRemoveBGExecutionRequestData(AddonExecutionGeneralRequestData):
    params: Optional[AddonRemoveBGExecutionParams]
