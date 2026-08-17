import pytest

from resume_ai.infrastructure.documents import DocumentReader
from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


@pytest.mark.parametrize(
    "content",
    [
        "Python e análise de dados".encode("utf-16"),
        "experiência".encode("latin-1"),
        b"Python\x00SQL",
        b"Python\x01SQL",
        b"Python\xffSQL",
    ],
    ids=["utf-16", "latin-1", "nul", "control", "invalid-byte"],
)
def test_rejects_non_utf8_or_binary_text(tmp_path, content: bytes) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError):
        validate_upload("resume.txt", content, settings)


def test_accepts_multilingual_utf8_with_line_controls(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    content = "Experiência\nPython\tSQL\r\nDados".encode()

    upload = validate_upload("currículo.txt", content, settings, "text/plain")

    assert upload.content == content
    assert upload.detected_type == "text/plain"


def test_document_reader_removes_utf8_bom(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    reader = DocumentReader(settings)

    text = reader.read_upload(
        "resume.txt",
        b"\xef\xbb\xbfPython e SQL",
        reported_type="text/plain; charset=utf-8",
    )

    assert text == "Python e SQL"
