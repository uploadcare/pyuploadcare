"""Re-record the file-tags and file-search VCR cassettes in one go.

These cassettes are recorded against permanent fixture files in a dedicated
project (see ``prepare_vcr_fixtures.py``). Doing it by hand is error prone in
three specific ways, which this script removes:

1. The tag-mutation tests drift the fixture's tags, so every module must be
   recorded starting from the ``[cat, animal]`` baseline. The fixture script
   is re-run before each module to reset it.
2. ``--vcr-record=all`` appends when a cassette already holds interactions,
   producing duplicate request/response pairs that replay in the wrong order.
   The target cassettes are deleted first, so each is written clean.
3. Replaying with real keys exported recomputes the signature tests against
   the wrong secret. The final verification pass runs with the keys removed
   from the environment, falling back to ``demosecretkey``.

Recording needs real keys; verification must not have them. Run:

    UPLOADCARE_PUBLIC_KEY=... UPLOADCARE_SECRET_KEY=... \
        poetry run python scripts/rerecord_cassettes.py

or ``make rerecord-cassettes``.

Recording happens before a test's assertions, so a module can be recorded
successfully even while its expectations still mismatch. The verification
pass at the end reports any such mismatches for you to reconcile; fix the
expected values and re-run.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREPARE = Path(__file__).resolve().parent / "prepare_vcr_fixtures.py"

# Each module and the cassettes it owns (deleted before recording so they are
# rewritten clean rather than appended to).
MODULES = [
    (
        "tests/functional/api/test_tags_api.py",
        "tests/functional/api/cassettes",
        [
            "test_get_file_tags",
            "test_get_empty_file_tags",
            "test_replace_file_tags",
            "test_update_file_tags",
        ],
    ),
    (
        "tests/functional/api/test_search_api.py",
        "tests/functional/api/cassettes",
        [
            "test_search_files_all",
            "test_search_files_empty_result",
            "test_search_files_with_appdata",
        ],
    ),
    (
        "tests/functional/resources/test_file_tags.py",
        "tests/functional/resources/cassettes",
        [
            "test_file_get_tags",
            "test_file_set_tags",
            "test_file_update_tags",
        ],
    ),
    (
        "tests/functional/ucare_cli/test_file_tags.py",
        "tests/functional/ucare_cli/cassettes",
        [
            "test_cli_get_file_tags",
            "test_cli_set_file_tags",
            "test_cli_update_file_tags",
        ],
    ),
    (
        "tests/functional/ucare_cli/test_search_files.py",
        "tests/functional/ucare_cli/cassettes",
        ["test_cli_search_files"],
    ),
]


def run(cmd, env=None):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def prepare_fixtures():
    return run([sys.executable, str(PREPARE)])


def main():
    pub_key = os.environ.get("UPLOADCARE_PUBLIC_KEY", "")
    if not pub_key or pub_key == "demopublickey":
        print(
            "Export the dedicated VCR project's real "
            "UPLOADCARE_PUBLIC_KEY/UPLOADCARE_SECRET_KEY (not the demo "
            "project) before recording."
        )
        return 1

    print("== Preparing fixtures and applying UUID substitutions ==")
    if prepare_fixtures() != 0:
        print("Fixture preparation failed; aborting.")
        return 1

    for module, cassette_dir, names in MODULES:
        print(f"\n== Recording {module} ==")

        # Reset the fixture's tags to baseline before each module.
        if prepare_fixtures() != 0:
            print("Fixture reset failed; aborting.")
            return 1

        # Delete this module's cassettes so recording writes them clean.
        for name in names:
            (ROOT / cassette_dir / f"{name}.yaml").unlink(missing_ok=True)

        run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--vcr-record=all",
                "-q",
                module,
            ]
        )

    print(
        "\n== Verifying replay without keys (falls back to demosecretkey) =="
    )
    replay_env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("UPLOADCARE_PUBLIC_KEY", "UPLOADCARE_SECRET_KEY")
    }
    code = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--vcr-record=none",
            "-q",
            "tests/functional",
        ],
        env=replay_env,
    )

    if code == 0:
        print(
            "\nAll functional tests pass on the fresh cassettes. Review the "
            "cassette diff, then commit the cassettes and manifest."
        )
    else:
        print(
            "\nReplay reported failures. The cassettes are recorded; the "
            "failures are expectation mismatches to reconcile in the test "
            "modules. Fix the expected values and re-run this script (or the "
            "single failing module with --vcr-record=all after deleting its "
            "cassettes)."
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
