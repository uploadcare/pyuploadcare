import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.convert_video import convert_video


@pytest.mark.vcr
def test_convert_video(uploadcare, capsys):
    convert_video(
        arg_namespace(
            "convert_video 72967d89-18bd-4906-a675-762ae721ccb5 "
            "--transformation size/640x480/add_padding/-/quality/lighter/ --store"
        ),
        uploadcare,
    )

    captured = capsys.readouterr()
    assert "uuid" in captured.out
    assert "thumbnails_group_uuid" in captured.out
