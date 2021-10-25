import pytest

from pyuploadcare.api.entities import Webhook


@pytest.mark.vcr
def test_client_create_webhook(uploadcare):
    webhook = uploadcare.create_webhook(
        target_url="https://webhook.site/699ba5a4-b178-41c7-b416-5d1b6739d052"
    )
    assert isinstance(webhook, Webhook)


@pytest.mark.vcr
def test_list_webhooks(uploadcare):
    webhooks = list(uploadcare.list_webhooks(limit=1))
    assert len(webhooks) == 1
    assert isinstance(webhooks[0], Webhook)


@pytest.mark.vcr
def test_update_webhook(uploadcare):
    webhook_id = 848006
    webhook = uploadcare.update_webhook(webhook_id, is_active=False)
    assert not webhook.is_active


@pytest.mark.vcr
def test_delete_webhook(uploadcare):
    webhook_id = 848006
    uploadcare.delete_webhook(webhook_id)
