from __future__ import annotations

import io

from docx import Document

from resume_ai.infrastructure.documents import DocumentReader
from resume_ai.settings import Settings


def _minimal_pdf(lines: list[str]) -> bytes:
    commands = ["BT /F1 12 Tf 72 720 Td 14 TL"]
    for index, line in enumerate(lines):
        commands.append(f"({line}) Tj" if index == 0 else f"T* ({line}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def _docx_bytes(lines: list[str]) -> bytes:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def test_txt_docx_pdf_extract_equivalent_semantic_lines(tmp_path) -> None:
    lines = ["Python", "FastAPI", "PostgreSQL"]
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        docling_enabled=False,
    )
    reader = DocumentReader(settings)
    extracted = {
        "txt": reader.read_upload("resume.txt", "\n".join(lines).encode("utf-8"), "text/plain"),
        "docx": reader.read_upload(
            "resume.docx",
            _docx_bytes(lines),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        "pdf": reader.read_upload("resume.pdf", _minimal_pdf(lines), "application/pdf"),
    }

    assert {
        kind: [line.strip() for line in text.splitlines() if line.strip()]
        for kind, text in extracted.items()
    } == {kind: lines for kind in extracted}
