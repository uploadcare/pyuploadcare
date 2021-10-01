from pyuploadcare.transformations.base import BaseTransformation, StrEnum


class DocumentFormat(StrEnum):
    pdf = "pdf"
    doc = "doc"
    docx = "docx"
    xls = "xls"
    xlsx = "xlsx"
    odt = "odt"
    ods = "ods"
    rtf = "rtf"
    txt = "txt"
    jpg = "jpg"
    enhanced_jpg = "enhanced.jpg"
    png = "png"


class DocumentTransformation(BaseTransformation):
    def format(self, file_format: DocumentFormat) -> "DocumentTransformation":
        self.set("format", [file_format])
        return self

    def page(self, page_number: int) -> "DocumentTransformation":
        self.set("page", [str(page_number)])
        return self

    def _prefix(self, file_id: str) -> str:
        return f"{file_id}/document/"
