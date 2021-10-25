from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser("convert_video", help="convert video")
    subparser.set_defaults(func=convert_video)
    subparser.add_argument("path", help="file path")
    subparser.add_argument(
        "--transformation",
        help="Video transformation string. Example: size/640x480/add_padding/-/quality/lighter/",
    )
    subparser.add_argument(
        "--store",
        action="store_true",
        default=False,
        dest="store",
        help="Store converted file",
    )
    return subparser


def convert_video(arg_namespace, client: Uploadcare) -> None:
    file = client.file(arg_namespace.path)

    kwargs = {}
    if arg_namespace.store:
        kwargs["store"] = True

    converted_file = file.convert_video(arg_namespace.transformation, **kwargs)

    info = converted_file.info
    info["thumbnails_group_uuid"] = converted_file.thumbnails_group_uuid
    pprint(info)
