#!/usr/bin/python
# coding: utf-8

from __future__ import unicode_literals

import argparse
import configparser
import logging
import os
import time
from typing import Any, Dict, List, Optional

from dateutil import parser

from pyuploadcare import __version__
from pyuploadcare.client import (
    DEFAULT_API_BASE,
    DEFAULT_API_VERSION,
    DEFAULT_UPLOAD_BASE,
    Uploadcare,
)
from pyuploadcare.exceptions import (
    TimeoutError,
    UploadcareException,
    UploadError,
)
from pyuploadcare.ucare_cli.sync import add_sync_files_parser
from pyuploadcare.ucare_cli.utils import bool_or_none, int_or_none, pprint


logger = logging.getLogger("pyuploadcare")

str_settings = (
    "public_key",
    "secret_key",
    "api_version",
    "api_base",
    "upload_base",
)
bool_settings = (
    "verify_api_ssl",
    "verify_upload_ssl",
)


def _list(api_list_method, arg_namespace, **extra):
    """A common function for building methods of the "list showing"."""
    if arg_namespace.starting_point:
        ordering_field = (arg_namespace.ordering or "").lstrip("-")
        if ordering_field in ("", "datetime_uploaded", "datetime_created"):
            arg_namespace.starting_point = parser.parse(
                arg_namespace.starting_point
            )

    items = api_list_method(
        starting_point=arg_namespace.starting_point,
        ordering=arg_namespace.ordering,
        limit=arg_namespace.limit,
        request_limit=arg_namespace.request_limit,
        **extra,
    )

    try:
        pprint([item.info() for item in items])
    except ValueError as e:
        print(e)


def list_files(arg_namespace, client: Uploadcare):
    return _list(
        client.list_files,
        arg_namespace,
        stored=arg_namespace.stored,
        removed=arg_namespace.removed,
    )


def list_groups(arg_namespace, client: Uploadcare):
    return _list(client.list_file_groups, arg_namespace)


def get_file(arg_namespace, client: Uploadcare):
    file = client.file(arg_namespace.path)
    pprint(file.info())


def store_files(arg_namespace, client: Uploadcare):
    client.store_files(arg_namespace.paths)
    _wait_if_needed(
        arg_namespace,
        client,
        lambda file: file.is_stored(),
        "timed out trying to store",
    )


def delete_files(arg_namespace, client: Uploadcare):
    client.delete_files(arg_namespace.paths)


def _wait_if_needed(arg_namespace, client: Uploadcare, check_func, error_msg):
    if not arg_namespace.wait:
        return

    for path in arg_namespace.paths:
        file_ = client.file(path)
        timeout = arg_namespace.timeout
        time_started = time.time()
        while not check_func(file_):
            if time.time() - time_started > timeout:
                raise TimeoutError(error_msg)
            file_.update_info()
            time.sleep(0.1)


def _check_upload_args(arg_namespace, client: Uploadcare):
    if not client.secret_key and (arg_namespace.store or arg_namespace.info):
        pprint('Cannot store or get info without "--secret" key')
        return False
    return True


def _handle_uploaded_file(file_, arg_namespace):
    if arg_namespace.store:
        file_.store()
        pprint("File stored successfully.")

    if arg_namespace.info:
        pprint(file_.info())

    if arg_namespace.cdnurl:
        pprint("CDN url: {0}".format(file_.cdn_url))


def upload_from_url(arg_namespace, client: Uploadcare):  # noqa: C901
    if not _check_upload_args(arg_namespace, client):
        return
    file_from_url = client.upload_from_url(arg_namespace.url)
    pprint(file_from_url)

    if arg_namespace.wait or arg_namespace.store:
        timeout = arg_namespace.timeout
        time_started = time.time()
        while time.time() - time_started < timeout:
            status = file_from_url.update_info()["status"]
            if status == "success":
                break
            if status in ("failed", "error"):
                raise UploadError(
                    "could not upload file from url: {0}".format(
                        file_from_url.info()
                    )
                )
            time.sleep(1)
        else:
            raise TimeoutError("timed out during upload")

    if arg_namespace.store or arg_namespace.info:
        file_ = file_from_url.get_file()
        if file_ is None:
            pprint("Cannot store or get info.")
            return

        _handle_uploaded_file(file_, arg_namespace)


def upload(arg_namespace, client: Uploadcare):
    if not _check_upload_args(arg_namespace, client):
        return
    with open(arg_namespace.filename, "rb") as fh:
        file_ = client.upload(fh)
        _handle_uploaded_file(file_, arg_namespace)


def create_group(arg_namespace, client: Uploadcare):
    files = [client.file(uuid) for uuid in arg_namespace.paths]
    group = client.create_file_group(files)
    pprint(group.info())


def ucare_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", action="version", version="ucare {0}".format(__version__)
    )

    subparsers = parser.add_subparsers()

    # files list
    subparser = subparsers.add_parser("list_files", help="list all files")
    subparser.set_defaults(func=list_files)
    subparser.add_argument(
        "--starting_point",
        help="a starting point for filtering files",
        action="store",
    )
    subparser.add_argument(
        "--ordering",
        help="specify the way the files should be sorted",
        action="store",
    )
    subparser.add_argument(
        "--limit", help="files to show", default=100, type=int_or_none
    )
    subparser.add_argument(
        "--request_limit",
        help="files per request",
        default=100,
        type=int_or_none,
    )
    subparser.add_argument(
        "--stored",
        help="filter stored files",
        choices=[True, False, None],
        type=bool_or_none,
        default=None,
    )
    subparser.add_argument(
        "--removed",
        help="filter removed files",
        choices=[True, False, None],
        type=bool_or_none,
        default=False,
    )

    # groups list
    subparser = subparsers.add_parser("list_groups", help="list all groups")
    subparser.set_defaults(func=list_groups)
    subparser.add_argument(
        "--starting_point",
        help="a starting point for filtering groups",
        action="store",
    )
    subparser.add_argument(
        "--ordering",
        help="specify the way the groups should be sorted",
        action="store",
    )
    subparser.add_argument(
        "--limit", help="group to show", default=100, type=int_or_none
    )
    subparser.add_argument(
        "--request_limit",
        help="groups per request",
        default=100,
        type=int_or_none,
    )

    # get
    subparser = subparsers.add_parser("get", help="get file info")
    subparser.set_defaults(func=get_file)
    subparser.add_argument("path", help="file path")

    # common store and delete args
    waiting_parent = argparse.ArgumentParser(add_help=False)
    waiting_parent.add_argument(
        "--timeout",
        type=int,
        dest="timeout",
        default=5,
        help="Set wait seconds until operation completed."
        " Default value is 5 seconds",
    )
    group = waiting_parent.add_mutually_exclusive_group()
    group.add_argument(
        "--wait",
        action="store_true",
        default=True,
        dest="wait",
        help="Wait for operation to be completed",
    )
    group.add_argument(
        "--nowait",
        action="store_false",
        dest="wait",
        help="Do not wait for operation to be completed",
    )

    # store
    subparser = subparsers.add_parser(
        "store", parents=[waiting_parent], help="store file"
    )
    subparser.set_defaults(func=store_files)
    subparser.add_argument("paths", nargs="+", help="file(s) path")

    # delete
    subparser = subparsers.add_parser(
        "delete", parents=[waiting_parent], help="request delete"
    )
    subparser.set_defaults(func=delete_files)
    subparser.add_argument("paths", nargs="+", help="file(s) path")

    # common upload args
    upload_parent = argparse.ArgumentParser(add_help=False)
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument(
        "--store",
        action="store_true",
        default=False,
        dest="store",
        help="Store uploaded file",
    )
    group.add_argument(
        "--nostore",
        action="store_false",
        dest="store",
        help="Do not store uploaded file",
    )
    group = upload_parent.add_mutually_exclusive_group()
    group.add_argument(
        "--info",
        action="store_true",
        default=False,
        dest="info",
        help="Get uploaded file info",
    )
    group.add_argument(
        "--noinfo",
        action="store_false",
        dest="info",
        help="Do not get uploaded file info",
    )
    upload_parent.add_argument(
        "--cdnurl", action="store_true", help="Store file and get CDN url."
    )

    # upload from url
    subparser = subparsers.add_parser(
        "upload_from_url", parents=[upload_parent], help="upload file from url"
    )
    subparser.set_defaults(func=upload_from_url)
    subparser.add_argument("url", help="file url")
    subparser.add_argument(
        "--timeout",
        type=int,
        dest="timeout",
        default=30,
        help="Set wait seconds file uploading from url."
        " Default value is 30 seconds",
    )
    group = subparser.add_mutually_exclusive_group()
    group.add_argument(
        "--wait",
        action="store_true",
        default=True,
        dest="wait",
        help="Wait for upload status",
    )
    group.add_argument(
        "--nowait",
        action="store_false",
        dest="wait",
        help="Do not wait for upload status",
    )

    # upload
    subparser = subparsers.add_parser(
        "upload", parents=[upload_parent], help="upload file"
    )
    subparser.set_defaults(func=upload)
    subparser.add_argument("filename", help="filename")

    # Create file group.
    subparser = subparsers.add_parser("create_group", help="create file group")
    subparser.set_defaults(func=create_group)
    subparser.add_argument("paths", nargs="+", help="file paths")

    # Sync files
    add_sync_files_parser(subparsers)

    # common arguments
    parser.add_argument(
        "--public_key",
        help="API key, if not set is read from uploadcare.ini"
        " and ~/.uploadcare config files",
    )
    parser.add_argument(
        "--secret_key",
        help="API secret, if not set is read from uploadcare.ini"
        " and ~/.uploadcare config files",
    )
    parser.add_argument(
        "--api_base",
        help="API url, can be read from uploadcare.ini"
        " and ~/.uploadcare config files."
        " Default value is {0}".format(DEFAULT_API_BASE),
    )
    parser.add_argument(
        "--upload_base",
        help="Upload API url, can be read from uploadcare.ini"
        " and ~/.uploadcare config files."
        " Default value is {0}".format(DEFAULT_UPLOAD_BASE),
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
        " Default value is {0}".format(DEFAULT_API_VERSION),
    )

    return parser


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


def load_config(
    arg_namespace: Optional[argparse.Namespace] = None,
    config_file_names: Optional[List[str]] = None,
):
    conf = {}

    if config_file_names:
        for file_name in config_file_names:
            conf = load_config_from_file(file_name, conf)

    if arg_namespace:
        conf = load_config_from_args(arg_namespace, conf)

    return conf


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
