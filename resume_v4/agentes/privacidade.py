from __future__ import annotations
import time
from resume_v4.models import ResultadoAgente
from resume_v4.services.privacidade import ServicoPrivacidade

class AgentePrivacidade:
    nome='Agente de Privacidade e Justiça'
    def __init__(self,servico: ServicoPrivacidade | None=None) -> None:
        self.servico=servico or ServicoPrivacidade()
    def executar(self,texto: str) -> ResultadoAgente:
        inicio=time.perf_counter(); resultado=self.servico.anonimizar(texto)
        return ResultadoAgente(
            agente=self.nome,
            resumo=f"{len(resultado.get('entidades',[]))} elementos pessoais foram detectados e removidos da análise técnica.",
            dados=resultado,
            confianca=0.92 if resultado.get('metodo')=='Microsoft Presidio' else 0.75,
            tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
