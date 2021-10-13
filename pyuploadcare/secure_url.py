import hashlib
import hmac
import time


class BaseSecureUrlBuilder:
    def generate_secure_url(self, uuid: str) -> str:
        raise NotImplementedError


class SecureUrlBuilder(BaseSecureUrlBuilder):
    template = "https://{cdn}/{uuid}/?token=exp={exp}~acl={acl}~hmac={token}"
    field_delimeter = "~"

    def __init__(
        self,
        cdn_url: str,
        secret_key: str,
        window: int = 300,
        hash_algo=hashlib.sha1,
    ):
        self.secret_key = secret_key
        self.cdn_url = cdn_url
        self.window = window
        self.hash_algo = hash_algo

    def generate_secure_url(self, uuid: str) -> str:
        uuid = uuid.lstrip("/").rstrip("/")

        expire = self.build_expire_time()

        acl = self._format_acl(uuid)

        token = self.build_token(acl, expire)

        secure_url = self.template.format(
            cdn=self.cdn_url, uuid=uuid, exp=expire, acl=acl, token=token
        )
        return secure_url

    def _format_acl(self, uuid: str) -> str:
        return f"/{uuid}/"

    def build_expire_time(self) -> int:
        return int(time.time()) + self.window

    def build_token(self, acl: str, expire: int) -> str:
        hash_source = [
            f"exp={expire}",
            f"acl={acl}",
        ]

        token = hmac.new(
            self.secret_key.encode(),
            self.field_delimeter.join(hash_source).encode(),
            self.hash_algo,
        ).hexdigest()

        return token
