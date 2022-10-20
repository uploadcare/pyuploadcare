from typing import Optional, Union
from unittest.mock import MagicMock

import pytest
from httpx import Headers

from pyuploadcare.exceptions import DEFAULT_RETRY_AFTER, ThrottledRequestError


def create_fake_response(
    status_code: int = 429,
    throttling_header_value: Optional[Union[str, int]] = None,
):
    magic_response = MagicMock()
    magic_response.status_code = status_code
    response_headers = Headers()

    if throttling_header_value is not None:
        response_headers["retry-after"] = str(throttling_header_value)

    magic_response.headers = response_headers
    return magic_response


@pytest.mark.parametrize("delay", (0, 1, 189))
def test_response_handler_for_positive_header_value(uploadcare, delay):
    fake_response = create_fake_response(throttling_header_value=delay)
    try:
        uploadcare.rest_client._perform_response(fake_response)
    except ThrottledRequestError as thre:
        assert thre.wait == delay + 1


def test_response_handler_for_absent_retry_after_header(uploadcare):
    fake_response = create_fake_response()
    try:
        uploadcare.rest_client._perform_response(fake_response)
    except ThrottledRequestError as thre:
        assert thre.wait == DEFAULT_RETRY_AFTER + 1


def test_response_handler_for_arbitrary_retry_header(uploadcare):
    fake_response = create_fake_response(throttling_header_value="convertion")
    try:
        uploadcare.rest_client._perform_response(fake_response)
    except ThrottledRequestError as thre:
        assert thre.wait == DEFAULT_RETRY_AFTER + 1
