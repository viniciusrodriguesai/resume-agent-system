import pytest

from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


def test_rejects_fake_pdf(tmp_path):
    settings = Settings(project_root=tmp_path, data_dir=tmp_path / "data", cache_dir=tmp_path / "cache")
    with pytest.raises(UnsafeUploadError):
        validate_upload("resume.pdf", b"not a pdf", settings)
