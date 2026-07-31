from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class ResultadoAgente:
    agente: str
    resumo: str
    dados: dict[str, Any] = field(default_factory=dict)
    alertas: list[str] = field(default_factory=list)
    confianca: float = 0.0
    tempo_ms: float = 0.0

    def dicionario(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Requisito:
    id: str
    texto: str
    prioridade: str
    categoria: str
    tipo: str = "competencia"
    aliases: list[str] = field(default_factory=list)
    origem: str = ""

@dataclass
class Evidencia:
    requisito_id: str
    trecho: str
    pontuacao_recuperacao: float
    pontuacao_reranker: float = 0.0
    metodo: str = "lexical"

@dataclass
class EstadoAnalise:
    analise_id: str
    curriculo_original: str
    vaga_original: str
    curriculo_anonimizado: str = ""
    resultado_documento: dict[str, Any] = field(default_factory=dict)
    resultado_privacidade: dict[str, Any] = field(default_factory=dict)
    perfil_curriculo: dict[str, Any] = field(default_factory=dict)
    perfil_vaga: dict[str, Any] = field(default_factory=dict)
    evidencias: list[dict[str, Any]] = field(default_factory=list)
    pontuacao: dict[str, Any] = field(default_factory=dict)
    revisao: dict[str, Any] = field(default_factory=dict)
    recomendacoes: list[dict[str, Any]] = field(default_factory=list)
    relatorio_markdown: str = ""
    relatorio_json: str = ""
    revisoes: int = 0
    rastreio: list[dict[str, Any]] = field(default_factory=list)
