from typing import Any, Dict

from pyuploadcare.client import Uploadcare
from pyuploadcare.dj.conf import config, user_agent_extension


def get_uploadcare_client():
    client_config: Dict[str, Any] = {
        "public_key": config["pub_key"],
        "secret_key": config["secret"],
        "user_agent_extension": user_agent_extension,
    }

    if config["cdn_base"]:
        client_config["cdn_base"] = config["cdn_base"]

    if config["upload_base_url"]:
        client_config["upload_base"] = config["upload_base_url"]

    return Uploadcare(**client_config)
