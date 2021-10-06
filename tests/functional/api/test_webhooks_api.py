import pytest

from pyuploadcare.api.entities import Webhook


@pytest.mark.vcr
def test_create_webhook(uploadcare):
    webhook = uploadcare.webhooks_api.create(
        {
            "event": "file.uploaded",
            "target_url": "https://webhook.site/699ba5a4-b178-41c7-b416-5d1b6739d052",
            "is_active": True,
        }
    )
    assert isinstance(webhook, Webhook)


@pytest.mark.vcr
def test_list_webhooks(uploadcare):
    webhooks = list(uploadcare.webhooks_api.list(limit=1))
    assert len(webhooks) == 1
    assert isinstance(webhooks[0], Webhook)


@pytest.mark.vcr
def test_update_webhook(uploadcare):
    webhook_id = 847096
    webhook = uploadcare.webhooks_api.update(webhook_id, {"is_active": False})
    assert not webhook.is_active


@pytest.mark.vcr
def test_delete_webhook(uploadcare):
    webhook_id = 847096
    uploadcare.webhooks_api.delete(webhook_id)
