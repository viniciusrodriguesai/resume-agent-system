from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from typing import Any
from resume_v4.config import Config

class Historico:
    def __init__(self, config: Config | None = None) -> None:
        self.config=config or Config(); self.config.preparar(); self._inicializar()

    def _inicializar(self) -> None:
        sql='CREATE TABLE IF NOT EXISTS analises (id TEXT PRIMARY KEY, criado_em TEXT NOT NULL, candidato TEXT, vaga TEXT, score INTEGER, nivel TEXT, dados_json TEXT NOT NULL)'
        with sqlite3.connect(self.config.banco_historico) as con:
            con.execute(sql)

    def salvar(self, analise_id: str, candidato: str, vaga: str, score: int, nivel: str, dados: dict[str, Any]) -> None:
        with sqlite3.connect(self.config.banco_historico) as con:
            con.execute(
                'INSERT OR REPLACE INTO analises VALUES (?,?,?,?,?,?,?)',
                (analise_id,datetime.now(timezone.utc).isoformat(),candidato,vaga,score,nivel,json.dumps(dados,ensure_ascii=False)),
            )

    def listar(self, limite: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.config.banco_historico) as con:
            rows=con.execute('SELECT id,criado_em,candidato,vaga,score,nivel FROM analises ORDER BY criado_em DESC LIMIT ?',(limite,)).fetchall()
        return [
            {'id':r[0],'criado_em':r[1],'candidato':r[2],'vaga':r[3],'score':r[4],'nivel':r[5]}
            for r in rows
        ]
