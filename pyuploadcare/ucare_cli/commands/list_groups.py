from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import _list, int_or_none


def register_arguments(subparsers):
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
    return subparser


def list_groups(arg_namespace, client: Uploadcare):
    return _list(client.list_file_groups, arg_namespace)
