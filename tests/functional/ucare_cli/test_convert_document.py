import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.convert_document import convert_document


@pytest.mark.vcr
def test_convert_document(uploadcare, capsys):
    convert_document(
        arg_namespace(
            "convert_document 2dcf583f-8de7-4b53-ae13-54c21bae39c5 --format png"
        ),
        uploadcare,
    )

    captured = capsys.readouterr()
    assert "uuid" in captured.out
