import pytest

from pyuploadcare.api.entities import ProjectInfo


@pytest.mark.vcr
def test_get_project_info(uploadcare):
    project_info = uploadcare.project_api.retrieve()
    assert isinstance(project_info, ProjectInfo)
