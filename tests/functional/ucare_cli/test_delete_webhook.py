import pytest

from pyuploadcare.ucare_cli.commands.delete_webhook import delete_webhook
from tests.functional.ucare_cli.helpers import arg_namespace


@pytest.mark.vcr
def test_delete_webhooks(capsys, uploadcare):
    delete_webhook(arg_namespace("delete_webhook 865565"), uploadcare)
