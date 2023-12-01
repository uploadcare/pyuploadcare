from tempfile import NamedTemporaryFile

import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.settings import load_config


@pytest.fixture
def config_file():
    return NamedTemporaryFile(mode="w+t", delete=False)


def test_use_pub_key_from_config_file(config_file):
    config_file.write("[ucare]\n" "pub_key = demopublickey")
    config_file.close()

    args = arg_namespace("list_files")
    conf = load_config(args, [config_file.name])

    assert conf["public_key"] == "demopublickey"


def test_redefine_pub_key_by_second_config_file(config_file):
    config_file.write("[ucare]\n" "pub_key = demopublickey")
    config_file.close()

    second_tmp_conf_file = NamedTemporaryFile(mode="w+t", delete=False)
    second_tmp_conf_file.write("[ucare]\n" "pub_key = demopublickey_modified")
    second_tmp_conf_file.close()

    args = arg_namespace("list_files")
    conf = load_config(args, [config_file.name, second_tmp_conf_file.name])

    assert conf["public_key"] == "demopublickey_modified"


def test_use_available_pub_key_from_config_files(config_file):
    config_file.write("[ucare]\n" "pub_key = demopublickey")
    config_file.close()

    second_tmp_conf_file = NamedTemporaryFile(mode="w+t", delete=False)
    second_tmp_conf_file.write("[ucare]\n" "secret = demosecretkey")
    second_tmp_conf_file.close()

    conf = load_config(
        arg_namespace("list_files"),
        [config_file.name, second_tmp_conf_file.name],
    )

    assert conf["public_key"] == "demopublickey"


def test_redefine_config_pub_key_by_args(config_file):
    config_file.write("[ucare]\n" "pub_key = demopublickey")
    config_file.close()

    conf = load_config(
        arg_namespace("--pub_key pub list_files"),
        [config_file.name],
    )

    assert conf["public_key"] == "pub"


def test_load_verify_api_ssl_false_value_from_config(config_file):
    config_file.write("[ucare]\n" "verify_api_ssl = false")
    config_file.close()

    conf = load_config(arg_namespace("list_files"), [config_file.name])

    assert not conf["verify_api_ssl"]


def test_load_verify_api_ssl_true_value_from_config(config_file):
    config_file.write("[ucare]\n" "verify_api_ssl = true")
    config_file.close()

    conf = load_config(arg_namespace("list_files"), [config_file.name])

    assert conf["verify_api_ssl"]


def test_redefine_config_verify_api_ssl_by_args(config_file):
    config_file.write("[ucare]\n" "verify_api_ssl = true")
    config_file.close()

    conf = load_config(
        arg_namespace("--no_check_api_certificate list_files"),
        [config_file.name],
    )

    assert not conf["verify_api_ssl"]
