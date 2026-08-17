import pytest

from resume_ai.infrastructure.security import UnsafeUploadError, validate_upload
from resume_ai.settings import Settings


@pytest.mark.parametrize(
    "filename",
    [
        "../resume.txt",
        "..\\resume.txt",
        "/absolute/resume.txt",
        "folder\\resume.txt",
        "resume\x00.txt",
        "resume\n.txt",
        "CON.txt",
        "lpt9.TXT",
        "resume?.txt",
        "resume.txt ",
        " resume.txt",
        "x" * 252 + ".txt",
        "",
    ],
)
def test_rejects_unsafe_filename(tmp_path, filename: str) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError):
        validate_upload(filename, b"valid UTF-8 text", settings)


def test_accepts_bounded_unicode_filename(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    upload = validate_upload("currículo técnico 2026.txt", "Olá".encode(), settings)

    assert upload.filename == "currículo técnico 2026.txt"
    assert upload.extension == ".txt"
    assert upload.detected_type == "text/plain"
