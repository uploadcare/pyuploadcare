"""Re-record the file-tags and file-search VCR cassettes in one go.

These cassettes are recorded against fixture files in a throwaway project
(see ``prepare_vcr_fixtures.py``). Doing it by hand is error prone in three
specific ways, which this script removes:

1. The tag-mutation tests drift the fixture's tags, so every module must be
   recorded starting from the ``[cat, animal]`` baseline. The fixture script
   is re-run before each module to reset it.
2. ``--vcr-record=all`` appends when a cassette already holds interactions,
   producing duplicate request/response pairs that replay in the wrong order.
   The target cassettes are deleted first, so each is written clean.
3. Replaying with real keys exported recomputes the signature tests against
   the wrong secret. The final verification pass runs with the keys removed
   from the environment, falling back to ``demosecretkey``.

Recording needs real keys; verification must not have them. The public key
is passed as the only argument, the secret key via the environment:

    UPLOADCARE_SECRET_KEY=... \
        uv run python scripts/rerecord_cassettes.py <public_key>

or ``UPLOADCARE_PUBLIC_KEY=... UPLOADCARE_SECRET_KEY=... make
rerecord-cassettes``.

Recording happens before a test's assertions, so a module can be recorded
successfully even while its expectations still mismatch. The verification
pass at the end reports any such mismatches for you to reconcile; fix the
expected values and re-run.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


ROOT = Path(__file__).resolve().parent.parent
PREPARE = Path(__file__).resolve().parent / "prepare_vcr_fixtures.py"

# Test modules to record; each owns the cassettes in its sibling
# ``cassettes/`` directory.
MODULES = [
    "tests/functional/api/test_tags_api.py",
    "tests/functional/api/test_search_api.py",
    "tests/functional/resources/test_file_tags.py",
    "tests/functional/ucare_cli/test_file_tags.py",
    "tests/functional/ucare_cli/test_search_files.py",
]

TEST_NAME = re.compile(r"^(?:async\s+)?def\s+(test_\w+)\s*\(", re.MULTILINE)
CASSETTE_NAME = re.compile(r"use_cassette\(\s*['\"]([^'\"]+)['\"]")


def cassette_names(module: Path) -> Set[str]:
    source = module.read_text(encoding="utf-8")
    return set(TEST_NAME.findall(source)) | set(CASSETTE_NAME.findall(source))


def delete_cassettes(module: Path) -> None:
    cassette_dir = module.parent / "cassettes"
    for name in cassette_names(module):
        (cassette_dir / f"{name}.yaml").unlink(missing_ok=True)


def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def prepare_fixtures(pub_key: str) -> int:
    return run([sys.executable, str(PREPARE), pub_key])


def main(argv: List[str]) -> int:
    if len(argv) != 2 or not argv[1] or argv[1] == "demopublickey":
        print(
            f"usage: {Path(argv[0]).name} <public_key>\n\n"
            "Pass the throwaway VCR project's public key (not the demo "
            "project) and export its UPLOADCARE_SECRET_KEY before recording."
        )
        return 1
    pub_key = argv[1]
    if not os.environ.get("UPLOADCARE_SECRET_KEY"):
        print("Export UPLOADCARE_SECRET_KEY before recording.")
        return 1

    record_env = dict(os.environ, UPLOADCARE_PUBLIC_KEY=pub_key)

    for module in MODULES:
        print(f"\n== Recording {module} ==")

        # Reset the fixture's tags to baseline before each module.
        if prepare_fixtures(pub_key) != 0:
            print("Fixture reset failed; aborting.")
            return 1

        delete_cassettes(ROOT / module)

        run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--vcr-record=all",
                "-q",
                module,
            ],
            env=record_env,
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
    sys.exit(main(sys.argv))
