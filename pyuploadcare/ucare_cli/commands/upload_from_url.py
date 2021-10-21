import time

from pyuploadcare.client import Uploadcare
from pyuploadcare.exceptions import TimeoutError, UploadError
from pyuploadcare.ucare_cli.commands.helpers import (
    _check_upload_args,
    _handle_uploaded_file,
    pprint,
)


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "upload_from_url", help="upload file from url"
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
                        file_from_url.info
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
