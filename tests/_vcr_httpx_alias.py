"""Early pytest plugin: alias `import httpx` to httpx2 before vcrpy loads."""

from httpx2 import alias_httpx


alias_httpx()
