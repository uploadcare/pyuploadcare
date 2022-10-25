from typing import Iterable
from uuid import uuid4

import pytest

from pyuploadcare.api.api import AddonAPI


@pytest.fixture()
def addon_api(uploadcare) -> Iterable[AddonAPI]:
    yield uploadcare.addons_api


def test_request_payload(addon_api: AddonAPI):
    file_uuid = uuid4()

    request_data = addon_api._get_request_data(str(file_uuid), None)
    assert request_data == {
        "target": str(file_uuid),
    }
