import pytest

from pyuploadcare.transformations.document import (
    DocumentFormat,
    DocumentTransformation,
)


@pytest.mark.vcr
def test_convert_document(uploadcare):
    transformation = DocumentTransformation().format(DocumentFormat.pdf)

    path = transformation.path("0e1cac48-1296-417f-9e7f-9bf13e330dcf")

    response = uploadcare.document_convert_api.convert([path])

    assert not response.problems

    document_convert_info = response.result[0]

    document_convert_status = uploadcare.document_convert_api.status(
        document_convert_info.token
    )

    assert document_convert_status.result.uuid


@pytest.mark.vcr
def test_convert_document_with_save_in_group(uploadcare):
    transformation = DocumentTransformation().format(DocumentFormat.jpg)

    path = transformation.path("da288a95-3029-4044-b902-5107e8579c5c")

    response = uploadcare.document_convert_api.convert(
        [path], save_in_group=True
    )

    assert not response.problems

    document_convert_info = response.result[0]

    document_convert_status = uploadcare.document_convert_api.status(
        document_convert_info.token
    )

    assert document_convert_status.result.uuid
