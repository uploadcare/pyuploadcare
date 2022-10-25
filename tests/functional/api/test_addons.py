from typing import Iterable
from uuid import uuid4

import pytest

from api.api import AddonAPI
from api.responses import AddonResponse


@pytest.fixture()
def addon_api(uploadcare) -> Iterable[AddonAPI]:
    yield uploadcare.addons_api


def test_request_payload(addon_api: AddonAPI):
    file_uuid = uuid4()

    request_data = addon_api._get_request_data(str(file_uuid), None)
    assert request_data == {
        "target": str(file_uuid),
    }


def test_status(secret_uploadcare):
    result: AddonResponse = secret_uploadcare.addons_api.status(
        request_id="ecd8f64a-d3d2-4d3a-89f7-b996c4992225",
        addon_name="aws_rekognition_detect_labels",
    )

    assert result.status == "done"
    assert result.result is None
