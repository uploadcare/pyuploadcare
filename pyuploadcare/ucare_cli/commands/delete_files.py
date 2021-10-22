from pyuploadcare.client import Uploadcare


def register_arguments(subparsers):
    subparser = subparsers.add_parser("delete", help="request delete")
    subparser.set_defaults(func=delete_files)
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


def delete_files(arg_namespace, client: Uploadcare):
    client.delete_files(arg_namespace.paths)
