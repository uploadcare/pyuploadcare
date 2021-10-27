import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.update_webhook import update_webhook


@pytest.mark.vcr
def test_update_webhooks(capsys, uploadcare):
    update_webhook(
        arg_namespace(
            "update_webhook 865715 --deactivate "
            "--target_url=https://webhook.site/updated"
        ),
        uploadcare,
    )
    captured = capsys.readouterr()
    assert '"is_active": false' in captured.out
