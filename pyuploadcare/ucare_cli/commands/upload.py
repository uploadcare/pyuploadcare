from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import (
    _check_upload_args,
    _handle_uploaded_file,
)


def register_arguments(subparsers):
    subparser = subparsers.add_parser("upload", help="upload file")
    subparser.set_defaults(func=upload)
    subparser.add_argument("filename", help="filename")
    group = subparser.add_mutually_exclusive_group()
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
    group = subparser.add_mutually_exclusive_group()
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
    subparser.add_argument(
        "--cdnurl", action="store_true", help="Store file and get CDN url."
    )
    return subparser


def upload(arg_namespace, client: Uploadcare):
    if not _check_upload_args(arg_namespace, client):
        return
    with open(arg_namespace.filename, "rb") as fh:
        file_ = client.upload(fh)
        _handle_uploaded_file(file_, arg_namespace)
