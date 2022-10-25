import hashlib
import os
import pickle
import re
import socket
import time
from math import ceil

from dateutil import parser
from httpx import HTTPError

from pyuploadcare import FileList, conf
from pyuploadcare.api.client import Client
from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import (
    bar,
    bool_or_none,
    int_or_none,
    pprint,
    promt,
)


def register_arguments(subparsers):
    subparser = subparsers.add_parser("sync", help="sync files")
    subparser.set_defaults(func=sync_files)
    subparser.add_argument(
        "path",
        nargs="?",
        help=(
            "Local path. It can contains special patterns like: {0} "
            "Default is {1}".format(
                " ".join(PATTERNS_MAPPING.keys()), DEFAULT_PATTERN_FILENAME
            )
        ),
        default=".",
    )
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
    subparser.add_argument(
        "--replace",
        help="replace exists files",
        default=False,
        action="store_true",
    )
    subparser.add_argument(
        "--uuids",
        nargs="+",
        help="list of file's uuids for sync",
    )
    subparser.add_argument(
        "--effects",
        help=(
            "apply effects for synced images."
            "Note that effects will apply to images only."
            "For more information look at: "
            "https://uploadcare.com/docs/processing/image/  "
            "Example: --effects=resize/200x/-/rotate/90/"
        ),
    )
    subparser.add_argument(
        "--no-input",
        help="do not ask for user input",
        default=False,
        action="store_true",
    )
    return subparser


def sync_files(arg_namespace, client: Uploadcare):  # noqa: C901
    if arg_namespace.starting_point:
        ordering_field = (arg_namespace.ordering or "").lstrip("-")
        if ordering_field in ("", "datetime_uploaded"):
            arg_namespace.starting_point = parser.parse(
                arg_namespace.starting_point
            )

    kwargs = dict(uuids=arg_namespace.uuids or None)
    if kwargs["uuids"] is None:
        kwargs.update(
            dict(
                starting_point=arg_namespace.starting_point,
                ordering=arg_namespace.ordering,
                limit=arg_namespace.limit,
                stored=arg_namespace.stored,
                removed=arg_namespace.removed,
                request_limit=arg_namespace.request_limit,
            )
        )

    with SyncSession(
        TrackedFileList(client=client, **kwargs),
        no_input=arg_namespace.no_input,
    ) as files:
        for f in files:
            if f.is_image and arg_namespace.effects:
                f.default_effects = arg_namespace.effects.lstrip("-/")

            local_filepath = build_filepath(arg_namespace.path, f)
            dirname = os.path.dirname(local_filepath)

            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)

            if os.path.exists(local_filepath) and not arg_namespace.replace:
                pprint(
                    "File `{0}` already exists. "
                    "To override it use `--replace` option".format(
                        local_filepath
                    )
                )
                continue

            url = f.cdn_url
            _download_file(url, local_filepath, file_size=f.size)


def _download_file(url: str, local_filepath: str, file_size: int, max_retry=3):
    client = Client(
        verify=conf.verify_api_ssl, timeout=get_timeout(conf.timeout)
    )

    for i in range(max_retry):
        try:
            with client.stream("GET", url) as response:
                if response is None:
                    pprint("Can't fetch URL: {0}".format(url))
                    pprint("Skip it.")
                    return

                save_file_locally(
                    fname=local_filepath,
                    response=response,
                    size=file_size,
                )

        except HTTPError as e:
            pprint("Connection Error: {0}".format(e))
            pprint("Retry..")
            time.sleep(i**2)
            continue
        else:
            break


def save_file_locally(fname, response, size):
    chunk_size = 1024
    with open(fname, "wb") as lf:
        for chunk in bar(
            response.iter_bytes(chunk_size),
            ceil(size / float(chunk_size)),
            fname,
        ):
            lf.write(chunk)


PATTERNS_REGEX = re.compile(r"(\${\w+})")
PATTERNS_MAPPING = {
    "${uuid}": lambda f: f.uuid,
    "${filename}": lambda f: f.filename,
    "${effects}": lambda f: f.default_effects,
    "${ext}": lambda f: os.path.splitext(f.filename or "")[-1],
}
DEFAULT_PATTERN_FILENAME = "${uuid}${ext}"


def build_filepath(path, file_):
    if not PATTERNS_REGEX.findall(path):
        path = os.path.join(path, DEFAULT_PATTERN_FILENAME)

    def _replace(mobj):
        pattern_name = mobj.group(0)
        if pattern_name in PATTERNS_MAPPING:
            pattern = PATTERNS_MAPPING[pattern_name]
            return pattern(file_)
        return pattern_name

    return os.path.normpath(PATTERNS_REGEX.sub(_replace, path))


class SyncSession:
    """Provides an ability to save current state of iteration if any errors
    happened during iteration. After that is possible to restore this state
    and continue from that point.
    """

    def __init__(self, file_list, no_input=False):
        parts = str(file_list.__dict__)
        self.session = file_list
        self.no_input = no_input
        self.signature = hashlib.md5(parts.encode("utf-8")).hexdigest()
        self.session_filepath = os.path.join(
            os.path.expanduser("~"), ".{0}.sync".format(self.signature)
        )

        # If the serialized session is exists load it and set as current
        if os.path.exists(self.session_filepath):
            if not self.no_input and promt("Continue last sync?"):
                with open(self.session_filepath, "rb") as f:
                    client = self.session._client
                    self.session = pickle.load(f)
                    self.session._client = client
                    return

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        if all(args):
            with open(self.session_filepath, "wb") as f:
                client = self.session._client
                self.session._client = None
                pickle.dump(self.session, f)
                self.session._client = client
            return False

        # Iteration is complete without errors.
        # Let's delete serialized session if exists.
        if os.path.exists(self.session_filepath):
            try:
                os.remove(self.session_filepath)
            except OSError:
                pass

        return True


class TrackedFileList(FileList):
    """Transparently iterate over provided list of UUIDs and all list
    of files of the user. Saves current state of iteration.
    """

    def __init__(self, *args, **kwargs):
        self.uuids = kwargs.pop("uuids", None)
        self.handled_uuids = []
        self.last_page_url = None
        super(TrackedFileList, self).__init__(*args, **kwargs)

    def __iter__(self):
        if self.uuids:
            yield from self.iter_uuids()
        else:
            for file in super().__iter__():
                if file.uuid not in self.handled_uuids:
                    yield file
                    self.handled_uuids.append(file.uuid)

    def iter_uuids(self):
        for uuid in self.uuids:
            if uuid in self.handled_uuids:
                continue
            yield self._client.file(uuid)
            self.handled_uuids.append(uuid)


def get_timeout(timeout):
    if timeout is not conf.DEFAULT:
        return timeout
    if conf.timeout is not conf.DEFAULT:
        return conf.timeout
    return socket.getdefaulttimeout()
