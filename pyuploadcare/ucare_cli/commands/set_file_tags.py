from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "set_file_tags", help="replace all file tags"
    )
    subparser.set_defaults(func=set_file_tags)
    subparser.add_argument("path", help="file path")
    subparser.add_argument(
        "tags",
        nargs="*",
        metavar="TAG",
        help="tags to set. Pass no tags to clear them",
    )
    return subparser


def set_file_tags(arg_namespace, client: Uploadcare):
    file = client.file(arg_namespace.path)
    response = file.set_tags(arg_namespace.tags)
    pprint(response.model_dump())
