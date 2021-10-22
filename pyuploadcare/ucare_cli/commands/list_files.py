from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import (
    _list,
    bool_or_none,
    int_or_none,
)


def register_arguments(subparsers):
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
    return subparser


def list_files(arg_namespace, client: Uploadcare):
    return _list(
        client.list_files,
        arg_namespace,
        stored=arg_namespace.stored,
        removed=arg_namespace.removed,
    )
