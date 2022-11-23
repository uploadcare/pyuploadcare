from typing import Iterable
from uuid import uuid4

import pytest

from pyuploadcare.api.api import AddonsAPI


@pytest.fixture()
def addons_api(uploadcare) -> Iterable[AddonsAPI]:
    yield uploadcare.addons_api


def test_request_payload(addons_api):
    file_uuid = uuid4()

    request_data = addons_api._get_request_data(str(file_uuid), None)
    assert request_data == {
        "target": str(file_uuid),
    }
