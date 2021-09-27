import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare import conf
from pyuploadcare.ucare_cli.main import main


@pytest.mark.vcr
def test_change_pub_key():
    main(arg_namespace("--pub_key demopublickey list_files"))

    assert conf.pub_key == "demopublickey"


@pytest.mark.vcr
def test_change_secret():
    main(arg_namespace("--secret demosecretkey list_files"))

    assert conf.secret == "demosecretkey"


@pytest.mark.vcr
def test_change_api_base():
    main(arg_namespace("--api_base https://uploadcare.com/api/ list_files"))

    assert conf.api_base == "https://uploadcare.com/api/"


@pytest.mark.vcr
def test_change_upload_base():
    main(
        arg_namespace(
            "--upload_base https://uploadcare.com/upload/ list_files"
        )
    )

    assert conf.upload_base == "https://uploadcare.com/upload/"


@pytest.mark.vcr
def test_change_verify_api_ssl():
    main(arg_namespace("list_files"))
    assert conf.verify_api_ssl

    main(arg_namespace("--no_check_api_certificate list_files"))
    assert not conf.verify_api_ssl


@pytest.mark.vcr
def test_change_verify_upload_ssl():
    main(arg_namespace("list_files"))
    assert conf.verify_upload_ssl

    main(arg_namespace("--no_check_upload_certificate list_files"))
    assert not conf.verify_upload_ssl


@pytest.mark.vcr
def test_change_api_version():
    main(arg_namespace("--api_version 0.777 list_files"))

    assert conf.api_version == "0.777"
