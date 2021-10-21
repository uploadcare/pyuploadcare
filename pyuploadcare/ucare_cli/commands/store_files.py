from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import _wait_if_needed


def register_arguments(subparsers):
    subparser = subparsers.add_parser("store", help="store file")
    subparser.set_defaults(func=store_files)
    subparser.add_argument("paths", nargs="+", help="file(s) path")
    subparser.add_argument(
        "--timeout",
        type=int,
        dest="timeout",
        default=5,
        help="Set wait seconds until operation completed."
        " Default value is 5 seconds",
    )
    group = subparser.add_mutually_exclusive_group()
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
    return subparser


def store_files(arg_namespace, client: Uploadcare):
    client.store_files(arg_namespace.paths)
    _wait_if_needed(
        arg_namespace,
        client,
        lambda file: file.is_stored(),
        "timed out trying to store",
    )
