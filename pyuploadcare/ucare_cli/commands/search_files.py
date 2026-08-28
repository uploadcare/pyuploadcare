from dateutil import parser as datetime_parser
from pydantic import ValidationError

from pyuploadcare.api.search_entities import FileSearchRequest, SearchSort
from pyuploadcare.client import Uploadcare
from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.ucare_cli.commands.helpers import (
    positive_int,
    pprint,
    strict_bool,
)


def register_arguments(subparsers):  # noqa: C901
    subparser = subparsers.add_parser("search_files", help="search files")
    subparser.set_defaults(func=search_files)

    subparser.add_argument(
        "--query",
        help="full text search across all searchable fields,"
        " at least 4 characters",
    )
    subparser.add_argument(
        "--fuzziness",
        action="store_true",
        default=None,
        help="allow approximate matches in the full text search",
    )

    for field in (
        "original_filename",
        "metadata",
        "detected_mime_type",
    ):
        subparser.add_argument(
            f"--phrase_{field}",
            help=f"ordered full text match on {field},"
            " at least 4 characters",
        )

    for field in ("uuid", "original_filename", "detected_mime_type"):
        subparser.add_argument(
            f"--exact_{field}",
            nargs="+",
            metavar="VALUE",
            help=f"exact match on {field}",
        )

    for bound in ("gt", "gte", "lt", "lte"):
        subparser.add_argument(
            f"--size_{bound}",
            type=int,
            metavar="BYTES",
            help=f"file size {bound} filter, in bytes",
        )
        subparser.add_argument(
            f"--uploaded_{bound}",
            type=datetime_parser.parse,
            metavar="DATETIME",
            help=f"upload datetime {bound} filter",
        )

    subparser.add_argument(
        "--is_image",
        type=strict_bool,
        metavar="true|false",
        help="filter images",
    )

    for name in ("any", "all", "none"):
        subparser.add_argument(
            f"--tags_{name}",
            nargs="+",
            metavar="TAG",
            help=f"match files having {name} of these tags",
        )

    subparser.add_argument(
        "--sort",
        action="append",
        choices=[key.value for key in SearchSort],
        help="sort key, repeat for up to 4 keys. Prefix with `-` for"
        " descending order, using the `--sort=-score` form so that the"
        " leading dash is not read as another option",
    )
    subparser.add_argument(
        "--limit",
        type=positive_int,
        default=100,
        help="total results to show. Defaults to 100; search cannot reach"
        " past the first 1000 results",
    )
    subparser.add_argument(
        "--request_limit",
        type=positive_int,
        default=20,
        help="results per request, 1 to 100. Defaults to 20."
        " You seldom need to change this",
    )
    subparser.add_argument(
        "--offset",
        type=int,
        help="results to skip before the first one shown",
    )
    subparser.add_argument(
        "--include_appdata",
        action="store_true",
        help="embed application data in every result",
    )
    return subparser


def _sub_condition(arg_namespace, prefix, fields):
    """Collect `--<prefix>_<field>` arguments into a nested dict."""
    condition = {
        field: getattr(arg_namespace, f"{prefix}_{field}", None)
        for field in fields
    }
    condition = {
        field: value for field, value in condition.items() if value is not None
    }
    return condition or None


def _build_request(arg_namespace) -> dict:
    request = {
        "query": arg_namespace.query,
        "fuzziness": arg_namespace.fuzziness,
        "is_image": arg_namespace.is_image,
        "sort": arg_namespace.sort,
        "phrase": _sub_condition(
            arg_namespace,
            "phrase",
            ("original_filename", "metadata", "detected_mime_type"),
        ),
        "exact": _sub_condition(
            arg_namespace,
            "exact",
            ("uuid", "original_filename", "detected_mime_type"),
        ),
        "size": _sub_condition(
            arg_namespace, "size", ("gt", "gte", "lt", "lte")
        ),
        "datetime_uploaded": _sub_condition(
            arg_namespace, "uploaded", ("gt", "gte", "lt", "lte")
        ),
        "tags": _sub_condition(arg_namespace, "tags", ("any", "all", "none")),
    }
    return {
        name: value for name, value in request.items() if value is not None
    }


def search_files(arg_namespace, client: Uploadcare):
    try:
        request = FileSearchRequest.model_validate(
            _build_request(arg_namespace)
        )
    except ValidationError as error:
        # `main()` only handles UploadcareException, so a raw ValidationError
        # would surface as a traceback.
        raise InvalidParamError(str(error))

    results = client.iterate_search_files(
        request,
        limit=arg_namespace.limit,
        request_limit=arg_namespace.request_limit,
        offset=arg_namespace.offset,
        include_appdata=arg_namespace.include_appdata,
    )
    pprint([result.model_dump() for result in results])
