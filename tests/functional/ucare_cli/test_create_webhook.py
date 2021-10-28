import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.create_webhook import create_webhook


@pytest.mark.vcr
def test_create_webhooks(capsys, uploadcare):
    create_webhook(
        arg_namespace(
            "create_webhook https://webhook.site/699ba5a4-b178-41c7-b416-5d1b6739d052 --active"
        ),
        uploadcare,
    )
    captured = capsys.readouterr()
    assert '"event": "file.uploaded"' in captured.out
