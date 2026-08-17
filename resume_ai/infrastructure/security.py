from __future__ import annotations

import io
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path

from resume_ai.settings import Settings


class UnsafeUploadError(ValueError):
    pass


@dataclass(frozen=True)
class SafeUpload:
    filename: str
    extension: str
    content: bytes
    detected_type: str


_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
_RESERVED_FILENAME_CHARACTERS = frozenset('<>:"/\\|?*')
_CANONICAL_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def _validate_filename(filename: str) -> str:
    if not filename or filename != filename.strip() or len(filename) > 255:
        raise UnsafeUploadError("Nome de arquivo inválido")
    if any(ord(character) < 32 or ord(character) == 127 for character in filename):
        raise UnsafeUploadError("Nome de arquivo contém caracteres de controle")
    if any(character in _RESERVED_FILENAME_CHARACTERS for character in filename):
        raise UnsafeUploadError("Nome de arquivo contém caracteres não permitidos")
    if Path(filename).stem.upper() in _WINDOWS_RESERVED_NAMES:
        raise UnsafeUploadError("Nome de arquivo reservado pelo sistema")
    return filename


def _is_safe_docx_entry(entry: zipfile.ZipInfo) -> bool:
    name = entry.filename
    if not name or len(name) > 512 or chr(92) in name or "\x00" in name or name.startswith("/"):
        return False
    parts = name.split("/")
    if entry.is_dir():
        parts = parts[:-1]
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return False
    if ":" in parts[0]:
        return False
    unix_mode = (entry.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(unix_mode):
        return False
    return entry.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}


def _looks_like_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 2_048:
                return False
            if any(not _is_safe_docx_entry(entry) for entry in entries):
                return False
            names = {entry.filename for entry in entries}
            if len(names) != len(entries):
                return False
            total_uncompressed = 0
            for entry in entries:
                if entry.flag_bits & 0x1:
                    return False
                total_uncompressed += entry.file_size
                if entry.file_size > 50 * 1024 * 1024 or total_uncompressed > 50 * 1024 * 1024:
                    return False
                compression_ratio = entry.file_size / max(entry.compress_size, 1)
                if entry.file_size > 1024 * 1024 and compression_ratio > 200:
                    return False
            return "word/document.xml" in names and "[Content_Types].xml" in names
    except (OSError, RuntimeError, zipfile.BadZipFile):
        return False


def _looks_like_pdf(content: bytes) -> bool:
    header = content[:8]
    if (
        len(header) != 8
        or not header.startswith(b"%PDF-")
        or header[5:6] not in {b"1", b"2"}
        or header[6:7] != b"."
        or not header[7:8].isdigit()
    ):
        return False
    eof_position = content.rfind(b"%%EOF")
    if eof_position < max(8, len(content) - 2_048):
        return False
    return not content[eof_position + len(b"%%EOF"):].strip(b" \t\r\n\f")


def validate_upload(
    filename: str,
    content: bytes,
    settings: Settings,
    reported_type: str | None = None,
) -> SafeUpload:
    safe_filename = _validate_filename(filename)
    extension = Path(safe_filename).suffix.lower()
    if extension not in settings.allowed_extensions:
        raise UnsafeUploadError(f"Extensão não permitida: {extension or 'sem extensão'}")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise UnsafeUploadError(f"Arquivo excede o limite de {settings.max_upload_mb} MB")
    if not content:
        raise UnsafeUploadError("Arquivo vazio")

    canonical_type = _CANONICAL_MIME_TYPES.get(extension)
    if canonical_type is None:
        raise UnsafeUploadError("Formato sem validação de conteúdo disponível")
    if reported_type:
        normalized_type = reported_type.partition(";")[0].strip().lower()
        if normalized_type != canonical_type:
            raise UnsafeUploadError("O tipo MIME declarado não corresponde ao formato do arquivo")

    if extension == ".pdf" and not _looks_like_pdf(content):
        raise UnsafeUploadError("A assinatura ou estrutura final do arquivo não corresponde a PDF")
    if extension == ".docx" and not _looks_like_docx(content):
        raise UnsafeUploadError("O arquivo não possui uma estrutura DOCX válida")
    if extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsafeUploadError("O TXT deve estar em UTF-8") from exc

    return SafeUpload(
        filename=safe_filename,
        extension=extension,
        content=content,
        detected_type=canonical_type,
    )
