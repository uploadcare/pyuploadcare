#!/usr/bin/python
# coding: utf-8

from __future__ import unicode_literals

import argparse
import logging

from pyuploadcare import __version__, conf
from pyuploadcare.client import Uploadcare
from pyuploadcare.exceptions import UploadcareException
from pyuploadcare.ucare_cli.commands import (
    convert_document,
    convert_video,
    create_group,
    create_webhook,
    delete_files,
    delete_webhook,
    get_file,
    get_project,
    list_files,
    list_groups,
    list_webhooks,
    store_files,
    sync,
    update_webhook,
    upload,
    upload_from_url,
)
from pyuploadcare.ucare_cli.commands.helpers import pprint
from pyuploadcare.ucare_cli.settings import load_config


logger = logging.getLogger("pyuploadcare")


def ucare_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", action="version", version="ucare {0}".format(__version__)
    )

    subparsers = parser.add_subparsers()

    list_files.register_arguments(subparsers)
    list_groups.register_arguments(subparsers)
    get_file.register_arguments(subparsers)
    store_files.register_arguments(subparsers)
    delete_files.register_arguments(subparsers)
    upload_from_url.register_arguments(subparsers)
    upload.register_arguments(subparsers)
    sync.register_arguments(subparsers)
    create_group.register_arguments(subparsers)
    convert_video.register_arguments(subparsers)
    get_project.register_arguments(subparsers)
    convert_document.register_arguments(subparsers)
    list_webhooks.register_arguments(subparsers)
    delete_webhook.register_arguments(subparsers)
    create_webhook.register_arguments(subparsers)
    update_webhook.register_arguments(subparsers)

    # common arguments
    parser.add_argument(
        "--pub_key",
        help="API key, if not set is read from uploadcare.ini"
        " and ~/.uploadcare config files",
    )
    parser.add_argument(
        "--secret",
        help="API secret, if not set is read from uploadcare.ini"
        " and ~/.uploadcare config files",
    )
    parser.add_argument(
        "--api_base",
        help="API url, can be read from uploadcare.ini"
        " and ~/.uploadcare config files."
        " Default value is {0}".format(conf.api_base),
    )
    parser.add_argument(
        "--upload_base",
        help="Upload API url, can be read from uploadcare.ini"
        " and ~/.uploadcare config files."
        " Default value is {0}".format(conf.upload_base),
    )
    parser.add_argument(
        "--no_check_upload_certificate",
        action="store_true",
        help="Don't check the uploading API server certificate."
        " Can be read from uploadcare.ini"
        " and ~/.uploadcare config files.",
    )
    parser.add_argument(
        "--no_check_api_certificate",
        action="store_true",
        help="Don't check the REST API server certificate."
        " Can be read from uploadcare.ini"
        " and ~/.uploadcare config files.",
    )
    parser.add_argument(
        "--api_version",
        help="API version, can be read from uploadcare.ini"
        " and ~/.uploadcare config files."
        " Default value is {0}".format(conf.api_version),
    )

    return parser


def main(  # noqa: C901
    arg_namespace=None, config_file_names=("~/.uploadcare", "uploadcare.ini")
):
    if arg_namespace is None:
        arg_namespace = ucare_argparser().parse_args()

    conf = load_config(arg_namespace, config_file_names)

    client = Uploadcare(**conf)

    if hasattr(arg_namespace, "func"):
        try:
            arg_namespace.func(arg_namespace, client)
        except UploadcareException as exc:
            pprint("ERROR: {0}".format(exc))


if __name__ == "__main__":
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    main()
