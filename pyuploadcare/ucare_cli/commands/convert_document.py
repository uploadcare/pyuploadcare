from pyuploadcare.client import Uploadcare
from pyuploadcare.transformations.document import (
    DocumentFormat,
    DocumentTransformation,
)
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "convert_document", help="convert document"
    )
    subparser.set_defaults(func=convert_document)
    subparser.add_argument("path", help="file path")
    subparser.add_argument(
        "--format",
        help="Document format",
        choices=[doc_format.value for doc_format in DocumentFormat],
    )
    subparser.add_argument(
        "--page",
        help="Document page",
        type=int,
    )
    subparser.add_argument(
        "--save-in-group",
        action="store_true",
        default=False,
        dest="save_in_group",
        help="Save pages of a multipage document to a group",
    )
    subparser.add_argument(
        "--store",
        action="store_true",
        default=False,
        dest="store",
        help="Store converted file",
    )
    return subparser


def convert_document(arg_namespace, client: Uploadcare) -> None:
    file = client.file(arg_namespace.path)

    transformation = DocumentTransformation()

    if arg_namespace.format:
        transformation.format(arg_namespace.format)

    if arg_namespace.page:
        transformation.format(arg_namespace.page)

    kwargs = {}

    if arg_namespace.store:
        kwargs["store"] = True

    if arg_namespace.save_in_group:
        kwargs["save_in_group"] = True

    converted_file = file.convert_document(transformation, **kwargs)

    info = converted_file.info
    pprint(info)
