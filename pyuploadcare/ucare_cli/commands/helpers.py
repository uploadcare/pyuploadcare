import json
import sys
import time
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dateutil import parser

from pyuploadcare.client import Uploadcare
from pyuploadcare.exceptions import TimeoutError


def _list(api_list_method, arg_namespace, **extra):
    """A common function for building methods of the "list showing"."""
    if arg_namespace.starting_point:
        ordering_field = (arg_namespace.ordering or "").lstrip("-")
        if ordering_field in ("", "datetime_uploaded", "datetime_created"):
            arg_namespace.starting_point = parser.parse(
                arg_namespace.starting_point
            )

    items = api_list_method(
        starting_point=arg_namespace.starting_point,
        ordering=arg_namespace.ordering,
        limit=arg_namespace.limit,
        request_limit=arg_namespace.request_limit,
        **extra,
    )

    try:
        pprint([item.info for item in items])
    except ValueError as e:
        print(e)


def _wait_if_needed(arg_namespace, client: Uploadcare, check_func, error_msg):
    if not arg_namespace.wait:
        return

    for path in arg_namespace.paths:
        file_ = client.file(path)
        timeout = arg_namespace.timeout
        time_started = time.time()
        while not check_func(file_):
            if time.time() - time_started > timeout:
                raise TimeoutError(error_msg)
            file_.update_info()
            time.sleep(0.1)


def _check_upload_args(arg_namespace, client: Uploadcare):
    if not client.secret_key and (arg_namespace.store or arg_namespace.info):
        pprint('Cannot store or get info without "--secret" key')
        return False
    return True


def _handle_uploaded_file(file_, arg_namespace):
    if arg_namespace.store:
        file_.store()
        pprint("File stored successfully.")

    if arg_namespace.info:
        pprint(file_.info)

    if arg_namespace.cdnurl:
        pprint("CDN url: {0}".format(file_.cdn_url))


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def pprint(value):
    print(json.dumps(value, indent=2, cls=Encoder))


def bool_or_none(value):
    return {"true": True, "false": False}.get(value)


def int_or_none(value):
    return None if value.lower() == "none" else int(value)


def promt(text, default="y"):
    return (input("{0} [y/n]: ".format(text)) or default) == "y"


def bar(iter_content, parts, title=""):
    """Iterates over the "iter_content" and draws a progress bar to stdout."""
    parts = max(float(parts), 1.0)
    cells = 10
    progress = 0
    step = cells / parts

    draw = lambda progress: sys.stdout.write(  # noqa: E731
        "\r[{0:10}] {1:.2f}% {2}".format(
            "#" * int(progress), progress * cells, title
        )
    )

    for chunk in iter_content:
        yield chunk

        progress += step
        draw(progress)
        sys.stdout.flush()

    draw(cells)
    print("")
