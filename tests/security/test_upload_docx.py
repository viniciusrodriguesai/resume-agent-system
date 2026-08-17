import io
import stat
import zipfile

import pytest

from resume_ai.infrastructure.security import (
    UnsafeUploadError,
    _is_safe_docx_entry,
    validate_upload,
)
from resume_ai.settings import Settings

_CONTENT_TYPES_XML = (
    '<Types><Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)


def _docx_with_entry(entry: zipfile.ZipInfo | str, content: str = "payload") -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            _CONTENT_TYPES_XML,
        )
        archive.writestr("word/document.xml", "<document />")
        archive.writestr(entry, content)
    return output.getvalue()


def _docx_with_xml(document_xml: str, content_types: str = _CONTENT_TYPES_XML) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document_xml)
    return output.getvalue()


@pytest.mark.parametrize(
    "entry_name",
    [
        "../../payload.txt",
        "word/../payload.txt",
        "/absolute/payload.txt",
        "C:/payload.txt",
        "word//payload.txt",
        "x" * 513,
    ],
)
def test_rejects_unsafe_docx_entry_name(tmp_path, entry_name: str) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="DOCX"):
        validate_upload("resume.docx", _docx_with_entry(entry_name), settings)


def test_rejects_docx_symlink_entry(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    symlink = zipfile.ZipInfo("word/link.xml")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16

    with pytest.raises(UnsafeUploadError, match="DOCX"):
        validate_upload("resume.docx", _docx_with_entry(symlink, "document.xml"), settings)


def test_rejects_docx_entry_with_windows_separator() -> None:
    entry = zipfile.ZipInfo("word/payload.txt")
    entry.filename = "word" + chr(92) + "payload.txt"

    assert not _is_safe_docx_entry(entry)


def test_rejects_docx_unsupported_compression(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    entry = zipfile.ZipInfo("word/unsupported.xml")
    entry.compress_type = zipfile.ZIP_BZIP2

    with pytest.raises(UnsafeUploadError, match="DOCX"):
        validate_upload("resume.docx", _docx_with_entry(entry), settings)


def test_accepts_bounded_docx_entries(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    upload = validate_upload(
        "resume.docx",
        _docx_with_entry("word/styles.xml", "<styles />"),
        settings,
    )

    assert upload.extension == ".docx"


@pytest.mark.parametrize(
    "document_xml",
    [
        '<!DOCTYPE document [<!ENTITY xxe SYSTEM "file:///private">]><document>&xxe;</document>',
        "<document><!entity expanded 'unsafe'></document>",
        " " * (64 * 1024 - 4) + "<!DOCTYPE document><document />",
    ],
    ids=["doctype", "entity", "chunk-boundary"],
)
def test_rejects_docx_with_unsafe_xml_declaration(tmp_path, document_xml: str) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="DOCX"):
        validate_upload("resume.docx", _docx_with_xml(document_xml), settings)


def test_rejects_docx_without_wordprocessing_content_type(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    with pytest.raises(UnsafeUploadError, match="DOCX"):
        validate_upload(
            "resume.docx",
            _docx_with_xml("<document />", "<Types />"),
            settings,
        )


def test_rejects_oversized_docx_content_types(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    oversized_content_types = _CONTENT_TYPES_XML + " " * (256 * 1024)

    with pytest.raises(UnsafeUploadError, match="DOCX"):
        validate_upload(
            "resume.docx",
            _docx_with_xml("<document />", oversized_content_types),
            settings,
        )
