__all__ = ["Client"]

import sys


version_vector = sys.version_info

if version_vector[:2] > (3, 6):
    from ._new_client import Client
else:
    from ._old_client import Client
