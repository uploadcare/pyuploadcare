import pytest

from pyuploadcare.ucare_cli.commands.list_webhooks import list_webhooks
from tests.functional.ucare_cli.helpers import arg_namespace


@pytest.mark.vcr
def test_list_webhooks(capsys, uploadcare):
    list_webhooks(arg_namespace("list_webhooks"), uploadcare)
    captured = capsys.readouterr()
    assert '"event": "file.uploaded"' in captured.out
