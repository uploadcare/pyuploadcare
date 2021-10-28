import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.get_project import get_project


@pytest.mark.vcr
def test_get_project(capsys, uploadcare):
    get_project(arg_namespace("get_project"), uploadcare)
    captured = capsys.readouterr()
    assert '"pub_key": ' in captured.out
