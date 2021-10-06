from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser("create_group", help="create file group")
    subparser.set_defaults(func=create_group)
    subparser.add_argument("paths", nargs="+", help="file paths")
    return subparser


def create_group(arg_namespace, client: Uploadcare):
    files = [client.file(uuid) for uuid in arg_namespace.paths]
    group = client.create_file_group(files)
    pprint(group.info)
