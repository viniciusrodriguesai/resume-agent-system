from __future__ import annotations
import io, tempfile
from pathlib import Path
from typing import Any
from resume_v4.config import Config

class LeitorDocumentos:
    def __init__(self, config: Config | None = None) -> None:
        self.config=config or Config()

    def ler_upload(self, arquivo: Any, nome: str) -> dict[str, Any]:
        conteudo=arquivo.getvalue(); sufixo=Path(nome).suffix.lower()
        if self.config.usar_docling:
            resultado=self._docling(conteudo,nome)
            if resultado: return resultado
        return self._fallback(conteudo,nome,sufixo)

    def _docling(self, conteudo: bytes, nome: str) -> dict[str, Any] | None:
        try:
            from docling.document_converter import DocumentConverter
        except Exception:
            return None
        with tempfile.NamedTemporaryFile(delete=False,suffix=Path(nome).suffix) as temporario:
            temporario.write(conteudo); caminho=Path(temporario.name)
        try:
            doc=DocumentConverter().convert(caminho).document
            return {'texto':doc.export_to_markdown(),'metodo':'Docling','nome':nome,'estrutura_preservada':True}
        except Exception:
            return None
        finally:
            caminho.unlink(missing_ok=True)

    def _fallback(self, conteudo: bytes, nome: str, sufixo: str) -> dict[str, Any]:
        if sufixo in {'.txt','.md'}:
            texto=conteudo.decode('utf-8',errors='replace')
        elif sufixo=='.pdf':
            from pypdf import PdfReader
            texto='\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(conteudo)).pages)
        elif sufixo=='.docx':
            from docx import Document
            doc=Document(io.BytesIO(conteudo)); texto='\n'.join(p.text for p in doc.paragraphs)
        else:
            raise ValueError('Formato não suportado. Use PDF, DOCX, TXT ou MD.')
        return {'texto':texto,'metodo':'Fallback local','nome':nome,'estrutura_preservada':False}
