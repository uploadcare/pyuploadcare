"""Early pytest plugin: alias `import httpx` to httpx2 before vcrpy loads.

TODO: remove once Python 3.8 and 3.9 support is dropped
"""

import sys


if sys.version_info >= (3, 10):
    from httpx2 import alias_httpx

    alias_httpx()
