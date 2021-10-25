import pytest

from pyuploadcare.api.entities import ProjectInfo


@pytest.mark.vcr
def test_client_get_project_info(uploadcare):
    project_info = uploadcare.get_project_info()
    assert isinstance(project_info, ProjectInfo)
