from resume_ai.infrastructure.documents import DocumentReader
from resume_ai.settings import Settings


def test_pdf_extraction_stops_after_character_limit(tmp_path, monkeypatch) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        max_document_chars=10,
    )
    reader = DocumentReader(settings)
    extracted_pages: list[int] = []

    class FakePage:
        def __init__(self, number: int, text: str) -> None:
            self.number = number
            self.text = text

        def extract_text(self) -> str:
            extracted_pages.append(self.number)
            return self.text

    class FakePdfReader:
        pages = [
            FakePage(1, "abcdef"),
            FakePage(2, "xyz123"),
            FakePage(3, "must-not-run"),
        ]

    monkeypatch.setattr("pypdf.PdfReader", lambda *_args, **_kwargs: FakePdfReader())

    text = reader._read_pdf(b"validated-pdf-placeholder")

    assert text == "abcdef\nxyz"
    assert len(text) == settings.max_document_chars
    assert extracted_pages == [1, 2]


def test_docx_extraction_stops_before_remaining_paragraphs_and_tables(tmp_path, monkeypatch) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        max_document_chars=10,
    )
    reader = DocumentReader(settings)
    extracted_paragraphs: list[int] = []

    class FakeParagraph:
        def __init__(self, number: int, value: str) -> None:
            self.number = number
            self.value = value

        @property
        def text(self) -> str:
            extracted_paragraphs.append(self.number)
            return self.value

    class FakeDocument:
        paragraphs = [
            FakeParagraph(1, "abcdef"),
            FakeParagraph(2, "xyz123"),
            FakeParagraph(3, "must-not-run"),
        ]

        @property
        def tables(self):
            raise AssertionError("tables must not be read after the character limit")

    monkeypatch.setattr("docx.Document", lambda *_args, **_kwargs: FakeDocument())

    text = reader._read_docx(b"validated-docx-placeholder")

    assert text == "abcdef\nxyz"
    assert len(text) == settings.max_document_chars
    assert extracted_paragraphs == [1, 2]
