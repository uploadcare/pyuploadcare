#!/usr/bin/env python

import os
import sys
from pathlib import Path

from django.core import management


git_root = Path(__file__).parent.parent.parent
sys.path.append(str(git_root))
sys.path.append(str(git_root / "tests"))


if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ["DJANGO_SETTINGS_MODULE"] = "test_project.settings"


if __name__ == "__main__":
    management.execute_from_command_line()
