import argparse
import configparser
import os
from typing import Any, Dict, List, Optional


str_settings = (
    "pub_key",
    "secret",
    "api_version",
    "api_base",
    "upload_base",
)
bool_settings = (
    "verify_api_ssl",
    "verify_upload_ssl",
)

client_setting_mapping = {
    "pub_key": "public_key",
    "secret": "secret_key",
}


def load_config_from_file(  # noqa: C901
    filename, conf: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if not conf:
        conf = {}

    filename = os.path.expanduser(filename)
    if not os.path.exists(filename):
        return conf

    config = configparser.RawConfigParser()
    config.read(filename)

    for name in str_settings:
        try:
            conf[name] = config.get("ucare", name)
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass
    for name in bool_settings:
        try:
            conf[name] = config.getboolean("ucare", name)
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

    return conf


def load_config_from_args(  # noqa: C901
    arg_namespace, conf: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if not conf:
        conf = {}

    for name in str_settings:
        arg = getattr(arg_namespace, name, None)
        if arg is not None:
            conf[name] = arg

    if arg_namespace and arg_namespace.no_check_upload_certificate:
        conf["verify_upload_ssl"] = False
    if arg_namespace and arg_namespace.no_check_api_certificate:
        conf["verify_api_ssl"] = False

    if getattr(arg_namespace, "cdnurl", False):
        arg_namespace.store = True

    return conf


def load_config(  # noqa: C901
    arg_namespace: Optional[argparse.Namespace] = None,
    config_file_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    conf: Dict[str, Any] = {}

    if config_file_names:
        for file_name in config_file_names:
            conf = load_config_from_file(file_name, conf)

    if arg_namespace:
        conf = load_config_from_args(arg_namespace, conf)

    client_conf = {}
    for key, value in conf.items():
        if key in client_setting_mapping:
            key = client_setting_mapping[key]
        client_conf[key] = value

    return client_conf
