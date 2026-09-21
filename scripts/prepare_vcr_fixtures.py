"""Create the permanent fixture files the VCR cassettes are recorded against.

The functional-test cassettes reference files by hard-coded UUIDs. This
script uploads those fixtures into a dedicated, long-lived test project and
prints the UUID substitutions for the test modules, so cassettes can be
re-recorded against the same files from then on (`--vcr-record=all`).

The created state mirrors what the tests assert:

- ``sunset-cat.jpg`` — the main fixture (tests call it ``FILE_UUID``):
  stored, tags ``cat, animal``, metadata ``album=summer sunset`` (the
  metadata must contain "sunset" so the search highlight on metadata is
  reproducible), ClamAV scanned (``include_appdata`` search test).
- ``no-tags.txt`` — stored, no tags (``test_get_empty_file_tags``).
- four more ``sunset-*.jpg`` tagged ``cat`` — with the main fixture they
  make five matches for ``query="sunset", tags all=[cat]``
  (``test_search_files`` asserts ``total == 5``). One of them is uploaded
  with ``store=False``: the second search result is asserted to have
  ``datetime_stored is None``.

Run it once against the dedicated project (never the demo project):

    UPLOADCARE_PUBLIC_KEY=... UPLOADCARE_SECRET_KEY=... \
        poetry run python scripts/prepare_vcr_fixtures.py

The resulting UUIDs are written to ``scripts/vcr_fixtures.json``. On later
runs the manifest is checked first and only missing files are recreated, so
the UUIDs — and therefore the cassettes — stay stable. Keep the manifest
committed and never delete the fixture files from the project.

NOTE: recording live also means the tags mutation tests (set/update) see
real state transitions, and two assertions encode states a real server
cannot produce (an untagged file matching ``all=[cat]``; a metadata
highlight absent from the stored metadata). Expect to reconcile expected
values in the test modules with the freshly recorded responses.
"""

import json
import os
import sys
from io import BytesIO
from pathlib import Path
from uuid import UUID

from pyuploadcare import Uploadcare
from pyuploadcare.api.addon_entities import AddonLabels
from pyuploadcare.exceptions import UploadcareException


MANIFEST = Path(__file__).parent / "vcr_fixtures.json"


def _as_uuid(value: object) -> str:
    """Canonical UUID string, or ValueError — sanitizes ids before file writes."""
    return str(UUID(str(value)))


# The UUIDs currently hard-coded in the test modules, to be replaced.
PLACEHOLDER_MAIN = "a55d6b25-d03c-4038-9838-6e06bb7df598"
PLACEHOLDER_NO_TAGS = "1a9c5240-7d9b-4473-851b-45fa4b0bed64"

# A valid 1x1 JPEG; `is_image` must be true for the search fixtures.
JPEG_1PX = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000"
    "ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f14"
    "1d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d"
    "38323c2e333432"
    "ffc0000b080001000101011100"
    "ffc4001f0000010501010101010100000000000000000102030405060708090a0b"
    "ffc400b5100002010303020403050504040000017d01020300041105122131410613"
    "516107227114328191a1082342b1c11552d1f02433627282090a161718191a2526"
    "2728292a3435363738393a434445464748494a535455565758595a636465666768"
    "696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7"
    "a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3"
    "e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9fa"
    "ffda0008010100003f00fbfa"
    "ffd9"
)

FIXTURES = [
    # key, filename, store, tags, metadata
    (
        "main",
        "sunset-cat.jpg",
        True,
        ["cat", "animal"],
        {"album": "summer sunset"},
    ),
    ("no_tags", "no-tags.txt", True, None, None),
    ("sunset_2", "sunset-beach.jpg", False, ["cat"], None),
    ("sunset_3", "sunset-hill.jpg", True, ["cat"], None),
    ("sunset_4", "sunset-pier.jpg", True, ["cat"], None),
    ("sunset_5", "sunset-lake.jpg", True, ["cat"], None),
]


def content_for(filename: str) -> BytesIO:
    if filename.endswith(".jpg"):
        data = JPEG_1PX
    else:
        data = b"vcr fixture: a file that carries no tags\n"
    buffer = BytesIO(data)
    buffer.name = filename
    return buffer


def upload(uploadcare: Uploadcare, filename: str, **kwargs):
    content = content_for(filename)
    # `size` spares `upload()` its `fileno()` stat, which BytesIO lacks.
    return uploadcare.upload(content, size=len(content.getvalue()), **kwargs)


def file_exists(uploadcare: Uploadcare, uuid: str) -> bool:
    try:
        uploadcare.files_api.retrieve(uuid)
        return True
    except UploadcareException:
        return False


# Which manifest key each placeholder UUID stands for in the test modules.
PLACEHOLDERS = {"main": PLACEHOLDER_MAIN, "no_tags": PLACEHOLDER_NO_TAGS}


def _fixture_replacements(old_uuids: dict, new_uuids: dict) -> dict:
    """Map each stale UUID (placeholder or prior manifest) to the current one."""
    replacements = {}
    for key, placeholder in PLACEHOLDERS.items():
        new = new_uuids.get(key)
        if not new:
            continue
        new = _as_uuid(new)
        sources = {placeholder}
        if old_uuids.get(key):
            sources.add(_as_uuid(old_uuids[key]))
        for old in sources:
            if old != new:
                replacements[old] = new
    return replacements


def _rewrite(path: str, replacements: dict) -> None:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    updated = text
    for old, new in replacements.items():
        updated = updated.replace(old, new)
    if updated != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(updated)
        print(f"substituted UUIDs in {path}")


def apply_substitutions(old_uuids: dict, new_uuids: dict) -> None:
    """Point the test modules at the current fixture UUIDs (idempotent)."""
    replacements = _fixture_replacements(old_uuids, new_uuids)
    if not replacements:
        return

    tests_dir = os.path.realpath(
        MANIFEST.parent.parent / "tests" / "functional"
    )
    for candidate in Path(tests_dir).rglob("*.py"):
        path = os.path.realpath(candidate)
        if path.startswith(tests_dir + os.sep):
            _rewrite(path, replacements)


def main() -> int:
    pub_key = os.environ.get("UPLOADCARE_PUBLIC_KEY", "")
    secret_key = os.environ.get("UPLOADCARE_SECRET_KEY", "")
    if not pub_key or not secret_key or pub_key == "demopublickey":
        print(
            "Set UPLOADCARE_PUBLIC_KEY/UPLOADCARE_SECRET_KEY to the "
            "dedicated VCR test project (not the demo project)."
        )
        return 1

    uploadcare = Uploadcare(public_key=pub_key, secret_key=secret_key)

    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    if manifest.get("pub_key", pub_key) != pub_key:
        print(
            f"Manifest was recorded against project "
            f"{manifest['pub_key']!r}, but the environment points at "
            f"{pub_key!r}. Refusing to mix projects."
        )
        return 1

    old_uuids = {
        key: _as_uuid(value)
        for key, value in manifest.get("files", {}).items()
    }
    uuids = dict(old_uuids)
    for key, filename, store, tags, metadata in FIXTURES:
        if key in uuids and file_exists(uploadcare, uuids[key]):
            print(f"{key}: exists, {uuids[key]} ({filename})")
            continue

        file = upload(
            uploadcare,
            filename,
            store=store,
            metadata=metadata,
            tags=tags,
        )
        uuids[key] = _as_uuid(file.uuid)
        print(f"{key}: uploaded {uuids[key]} ({filename})")

    # The tags mutation tests are recorded against the main fixture; make
    # sure its tags are at the baseline the read-only tests assert.
    uploadcare.tags_api.set(uuids["main"], ["cat", "animal"])

    # `test_search_files_with_appdata` asserts a ClamAV scan result on the
    # first `all=[cat]` match; scan every stored cat fixture to be safe.
    for key, filename, store, tags, _metadata in FIXTURES:
        if store and tags and "cat" in tags:
            try:
                uploadcare.addons_api.execute(uuids[key], AddonLabels.CLAM_AV)
                print(f"{key}: ClamAV scan requested")
            except UploadcareException as exc:
                print(f"{key}: ClamAV scan failed: {exc}")

    MANIFEST.write_text(
        json.dumps({"pub_key": pub_key, "files": uuids}, indent=2) + "\n"
    )
    print(f"\nManifest written to {MANIFEST}")

    apply_substitutions(old_uuids, uuids)

    print("\nSearch indexing lags uploads; wait a minute before recording the")
    print("search module. query='sunset' + tags all=[cat] should return 5.")
    print("\nUse scripts/rerecord_cassettes.py (or `make rerecord-cassettes`)")
    print("to record every module and verify replay in one go.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
