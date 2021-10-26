from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "create_webhook", help="create file group"
    )
    subparser.set_defaults(func=create_webhook)
    subparser.add_argument("target_url", nargs="+", help="file paths")
    subparser.add_argument("--active", action="store_true")
    subparser.add_argument("--event", default="file.uploaded")
    return subparser


def create_webhook(arg_namespace, client: Uploadcare):
    webhook = client.create_webhook(
        target_url=arg_namespace.target_url,
        is_active=arg_namespace.active,
        event=arg_namespace.event,
    )
    pprint(webhook.dict())
