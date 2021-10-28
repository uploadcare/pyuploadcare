from pyuploadcare import ProjectInfo
from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser("get_project", help="get project info")
    subparser.set_defaults(func=get_project)
    return subparser


def get_project(arg_namespace, client: Uploadcare):
    project: ProjectInfo = client.get_project_info()
    pprint(project.dict())
