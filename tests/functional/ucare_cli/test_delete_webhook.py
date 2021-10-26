import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.delete_webhook import delete_webhook


@pytest.mark.vcr
def test_delete_webhooks(capsys, uploadcare):
    delete_webhook(arg_namespace("delete_webhook 865565"), uploadcare)
