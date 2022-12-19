from unittest.mock import Mock

import pytest

from pyuploadcare.api import WebhooksAPI
from pyuploadcare.exceptions import InvalidRequestError, WebhookIsNotUnique


ERROR_MESSAGE_FOR_COLLISION = """
    "non_field_errors":["This project is already subscribed on this event"]
""".replace(
    "\n", ""
)


def get_raising_client(decoded_content):
    error = InvalidRequestError(decoded_content)
    return Mock(put=Mock(side_effect=error), post=Mock(side_effect=error))


def test_exception_wrapping_on_webhook_update():
    client = get_raising_client(ERROR_MESSAGE_FOR_COLLISION)
    wh_api = WebhooksAPI(
        client=client, public_key="", secret_key="", signed_uploads_ttl=0
    )

    with pytest.raises(WebhookIsNotUnique):
        wh_api.update("uuid", data={})


def test_exception_wrapping_on_webhook_create():
    client = get_raising_client(ERROR_MESSAGE_FOR_COLLISION)
    wh_api = WebhooksAPI(
        client=client, public_key="", secret_key="", signed_uploads_ttl=0
    )

    with pytest.raises(WebhookIsNotUnique):
        wh_api.create(data={})
