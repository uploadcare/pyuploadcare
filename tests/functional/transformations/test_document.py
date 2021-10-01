from pyuploadcare.transformations.document import (
    DocumentFormat,
    DocumentTransformation,
)


def test_document_transformation():
    transformation = DocumentTransformation().format(DocumentFormat.pdf)

    assert transformation.path("a6efd840-076f-4227-9073-bbaef16cfe35") == (
        "a6efd840-076f-4227-9073-bbaef16cfe35/document/-/format/pdf/"
    )


def test_document_transformation_page():
    transformation = (
        DocumentTransformation().format(DocumentFormat.jpg).page(2)
    )

    assert transformation.path("a6efd840-076f-4227-9073-bbaef16cfe35") == (
        "a6efd840-076f-4227-9073-bbaef16cfe35/document/-/format/jpg/-/page/2/"
    )


def test_document_transformation_custom_parameter():
    transformation = (
        DocumentTransformation()
        .format(DocumentFormat.jpg)
        .set("custom", ["a", "b"])
    )

    assert transformation.path("a6efd840-076f-4227-9073-bbaef16cfe35") == (
        "a6efd840-076f-4227-9073-bbaef16cfe35/document/-/format/jpg/-/custom/a/b/"
    )
