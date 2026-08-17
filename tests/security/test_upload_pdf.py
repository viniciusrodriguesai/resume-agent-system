import pytest

from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


@pytest.mark.parametrize(
    "content",
    [
        b"%PDF-1.7 truncated",
        b"%PDF-9.9\n%%EOF",
        b"%PDF-1.7\n%%EOF<script>alert(1)</script>",
        b"%PDF-1.7\n%%EOF" + b" " * 2_049,
        b"not-a-pdf\n%%EOF",
    ],
)
def test_rejects_incomplete_or_tailed_pdf(tmp_path, content: bytes) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="PDF"):
        validate_upload("resume.pdf", content, settings)


@pytest.mark.parametrize(
    "content",
    [
        b"%PDF-1.7\n%binary\xff\n%%EOF\r\n",
        b"%PDF-2.0\n%%EOF\n",
    ],
)
def test_accepts_supported_pdf_header_and_final_marker(tmp_path, content: bytes) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    upload = validate_upload("resume.pdf", content, settings, "application/pdf")

    assert upload.extension == ".pdf"
    assert upload.detected_type == "application/pdf"
