from pyuploadcare.client import Uploadcare
from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "update_file_tags", help="add and/or delete file tags"
    )
    subparser.set_defaults(func=update_file_tags)
    subparser.add_argument("path", help="file path")
    subparser.add_argument(
        "--add",
        nargs="+",
        metavar="TAG",
        help="tags to add",
    )
    subparser.add_argument(
        "--delete",
        nargs="+",
        metavar="TAG",
        help="tags to delete",
    )
    return subparser


def update_file_tags(arg_namespace, client: Uploadcare):
    if arg_namespace.add is None and arg_namespace.delete is None:
        raise InvalidParamError(
            "nothing to do: pass at least one of --add or --delete"
        )

    file = client.file(arg_namespace.path)
    response = file.update_tags(
        add=arg_namespace.add, delete=arg_namespace.delete
    )
    pprint(response.model_dump())
