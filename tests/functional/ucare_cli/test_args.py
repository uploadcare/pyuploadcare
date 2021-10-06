from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.settings import load_config


def test_change_pub_key():
    conf = load_config(arg_namespace("--pub_key demopublickey list_files"))

    assert conf["public_key"] == "demopublickey"


def test_change_secret():
    conf = load_config(arg_namespace("--secret demosecretkey list_files"))

    assert conf["secret_key"] == "demosecretkey"


def test_change_api_base():
    conf = load_config(
        arg_namespace("--api_base https://uploadcare.com/api/ list_files")
    )

    assert conf["api_base"] == "https://uploadcare.com/api/"


def test_change_upload_base():
    conf = load_config(
        arg_namespace(
            "--upload_base https://uploadcare.com/upload/ list_files"
        )
    )

    assert conf["upload_base"] == "https://uploadcare.com/upload/"


def test_change_verify_api_ssl():
    conf = load_config(arg_namespace("list_files"))
    assert "verify_api_ssl" not in conf

    conf = load_config(arg_namespace("--no_check_api_certificate list_files"))
    assert not conf["verify_api_ssl"]


def test_change_verify_upload_ssl():
    conf = load_config(arg_namespace("list_files"))
    assert "verify_upload_ssl" not in conf

    conf = load_config(
        arg_namespace("--no_check_upload_certificate list_files")
    )
    assert not conf["verify_upload_ssl"]


def test_change_api_version():
    conf = load_config(arg_namespace("--api_version 0.777 list_files"))

    assert conf["api_version"] == "0.777"
