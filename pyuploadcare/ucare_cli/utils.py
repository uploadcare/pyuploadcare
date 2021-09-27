# coding: utf-8
from __future__ import unicode_literals

import json
import sys
from datetime import datetime
from uuid import UUID


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
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
