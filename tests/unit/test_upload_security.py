import io
import zipfile

import pytest

from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


def test_rejects_fake_pdf(tmp_path):
    settings = Settings(project_root=tmp_path, data_dir=tmp_path / "data", cache_dir=tmp_path / "cache")
    with pytest.raises(UnsafeUploadError):
        validate_upload("resume.pdf", b"not a pdf", settings)


def test_rejects_docx_zip_bomb(tmp_path):
    settings = Settings(project_root=tmp_path, data_dir=tmp_path / "data", cache_dir=tmp_path / "cache")
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "A" * (2 * 1024 * 1024))

    with pytest.raises(UnsafeUploadError):
        validate_upload("resume.docx", content.getvalue(), settings)
