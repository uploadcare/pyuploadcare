import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.main import main


@pytest.mark.vcr
def test_get_file_by_uuid(capsys):
    main(arg_namespace("get 638d0296-fda1-4102-9b18-d28b37494298"))
    captured = capsys.readouterr()
    assert '"uuid": "638d0296-fda1-4102-9b18-d28b37494298"' in captured.out


@pytest.mark.vcr
def test_get_file_by_cdn_url(capsys):
    main(
        arg_namespace(
            "get https://ucarecdn.com/638d0296-fda1-4102-9b18-d28b37494298/"
        )
    )
    captured = capsys.readouterr()
    assert '"uuid": "638d0296-fda1-4102-9b18-d28b37494298"' in captured.out
