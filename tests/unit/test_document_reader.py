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
