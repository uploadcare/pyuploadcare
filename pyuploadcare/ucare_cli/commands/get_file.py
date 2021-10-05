from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser("get", help="get file info")
    subparser.set_defaults(func=get_file)
    subparser.add_argument("path", help="file path")
    return subparser


def get_file(arg_namespace, client: Uploadcare):
    file = client.file(arg_namespace.path)
    pprint(file.info)
