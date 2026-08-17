import pytest

from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


@pytest.mark.parametrize(
    "filename",
    ["resume.exe", "resume.pdf.exe", "resume", "resume.csv"],
)
def test_rejects_disallowed_or_missing_extension(tmp_path, filename: str) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="Extensão"):
        validate_upload(filename, b"content", settings)


def test_rejects_empty_upload(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="vazio"):
        validate_upload("resume.txt", b"", settings)


def test_rejects_oversized_upload_before_format_parsing(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        max_upload_mb=1,
    )

    with pytest.raises(UnsafeUploadError, match="limite"):
        validate_upload("resume.pdf", b"x" * (1024 * 1024 + 1), settings)


def test_accepts_text_upload_at_exact_size_limit(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        max_upload_mb=1,
    )
    content = b"x" * (1024 * 1024)

    upload = validate_upload("RESUME.TXT", content, settings)

    assert len(upload.content) == 1024 * 1024
    assert upload.extension == ".txt"
