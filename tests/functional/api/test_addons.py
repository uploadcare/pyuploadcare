from uuid import uuid4

import pytest

from pyuploadcare.api.addon_entities import (
    AddonClamAVExecutionParams,
    AddonLabels,
    AddonRemoveBGExecutionParams,
)
from pyuploadcare.api.api import AddonsAPI


@pytest.fixture()
def addons_api(uploadcare) -> AddonsAPI:
    return uploadcare.addons_api


def test_request_payload(addons_api):
    file_uuid = uuid4()

    params = AddonRemoveBGExecutionParams(
        crop=True,  # should be present
        scale=None,  # should be left out
    )

    request_data = addons_api._get_request_data(str(file_uuid), params)
    assert request_data == {
        "target": str(file_uuid),
        "params": {
            "crop": True,
        },
    }


@pytest.mark.vcr
def test_aws_rekognition_detect_labels_execute(uploadcare):
    result = uploadcare.addons_api.execute(
        "485f5c0e-3567-46b1-a5c9-96a8ffc45713",
        AddonLabels.AWS_LABEL_RECOGNITION,
    )
    assert str(result.request_id) == "6e8424be-749a-4eee-bc1e-05393a7b6938"


@pytest.mark.vcr
def test_aws_rekognition_detect_labels_status(uploadcare):
    result = uploadcare.addons_api.status(
        "6e8424be-749a-4eee-bc1e-05393a7b6938",
        AddonLabels.AWS_LABEL_RECOGNITION,
    )
    assert result.status


@pytest.mark.vcr
def test_aws_rekognition_detect_moderation_labels_execute(uploadcare):
    assert (
        AddonLabels.AWS_MODERATION_LABELS.value
        == "aws_rekognition_detect_moderation_labels"
    )
    result = uploadcare.addons_api.execute(
        "485f5c0e-3567-46b1-a5c9-96a8ffc45713",
        "aws_rekognition_detect_moderation_labels",  # String values should work here too
    )
    assert str(result.request_id) == "6666a652-a79d-4991-9c4b-3f7705ed7c6c"


@pytest.mark.vcr
def test_aws_rekognition_detect_moderation_labels_status(uploadcare):
    result = uploadcare.addons_api.status(
        "6666a652-a79d-4991-9c4b-3f7705ed7c6c",
        "aws_rekognition_detect_moderation_labels",  # String values should work here too
    )
    assert result.status


@pytest.mark.vcr
def test_clam_av_execute(uploadcare):
    params = AddonClamAVExecutionParams(purge_infected=False)
    result = uploadcare.addons_api.execute(
        "485f5c0e-3567-46b1-a5c9-96a8ffc45713", AddonLabels.CLAM_AV, params
    )
    assert str(result.request_id) == "865e5d23-f602-4338-8d3c-fb22f599aa27"


@pytest.mark.vcr
def test_clam_av_status(uploadcare):
    result = uploadcare.addons_api.status(
        "865e5d23-f602-4338-8d3c-fb22f599aa27",
        AddonLabels.CLAM_AV,
    )
    assert result.status


@pytest.mark.vcr
def test_remove_bg_execute(uploadcare):
    params = AddonRemoveBGExecutionParams(
        crop=True,
        add_shadow=True,
    )
    result = uploadcare.addons_api.execute(
        "485f5c0e-3567-46b1-a5c9-96a8ffc45713", AddonLabels.REMOVE_BG, params
    )
    assert str(result.request_id) == "53930d55-8ecb-4b2b-ab9e-3c3b1ffe53cb"


@pytest.mark.vcr
def test_remove_bg_status(uploadcare):
    result = uploadcare.addons_api.status(
        "53930d55-8ecb-4b2b-ab9e-3c3b1ffe53cb",
        AddonLabels.REMOVE_BG,
    )
    assert result.status
