import io
import zipfile

import pytest

from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


def _minimal_docx() -> bytes:
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
    return content.getvalue()


@pytest.mark.parametrize(
    ("filename", "content", "reported_type"),
    [
        ("resume.txt", b"plain text", "image/png"),
        ("resume.pdf", b"%PDF-1.4\n%%EOF", "text/plain"),
        ("resume.docx", _minimal_docx(), "application/zip"),
    ],
)
def test_rejects_declared_mime_mismatch(
    tmp_path,
    filename: str,
    content: bytes,
    reported_type: str,
) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="MIME"):
        validate_upload(filename, content, settings, reported_type)


def test_accepts_normalized_declared_mime(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    upload = validate_upload(
        "resume.txt",
        "currículo".encode(),
        settings,
        " Text/Plain; charset=UTF-8 ",
    )

    assert upload.detected_type == "text/plain"


def test_declared_mime_cannot_replace_content_validation(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="assinatura"):
        validate_upload("resume.pdf", b"not a pdf", settings, "application/pdf")


def test_rejects_configured_extension_without_validator(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        allowed_extensions=(".rtf",),
    )

    with pytest.raises(UnsafeUploadError, match="sem validação"):
        validate_upload("resume.rtf", b"{\\rtf1 resume}", settings)
