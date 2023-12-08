from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "list_webhooks", help="list all webhooks"
    )
    subparser.set_defaults(func=list_webhooks)
    return subparser


def list_webhooks(arg_namespace, client: Uploadcare):
    webhooks = [webhook.model_dump() for webhook in client.list_webhooks()]
    pprint(webhooks)
