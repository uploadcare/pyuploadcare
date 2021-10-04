import os
import sys
from pathlib import Path

import django


sys.path.append(str(Path(__file__).parent.parent))

os.environ["DJANGO_SETTINGS_MODULE"] = "test_project.settings"

django.setup()
