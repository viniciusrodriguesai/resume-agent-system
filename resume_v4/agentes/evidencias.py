from __future__ import annotations
import time
from resume_v4.models import ResultadoAgente
from resume_v4.services.semantica import MotorSemantico

class AgenteEvidencias:
    nome='Agente de Recuperação e Reranqueamento'
    def __init__(self,motor: MotorSemantico | None=None) -> None:
        self.motor=motor or MotorSemantico()

    def executar(self,perfil_curriculo: dict,perfil_vaga: dict,top_k: int=5) -> ResultadoAgente:
        inicio=time.perf_counter(); trechos=perfil_curriculo.get('trechos',[]); saida=[]
        for requisito in perfil_vaga.get('requisitos',[]):
            consulta=' | '.join([requisito['texto'],*requisito.get('aliases',[])])
            candidatos=self.motor.recuperar(consulta,trechos,top_k=top_k)
            reranqueados=self.motor.reranquear(consulta,candidatos)
            melhor=reranqueados[0] if reranqueados else {'trecho':'','score_recuperacao':0.0,'score_reranker':0.0,'metodo':'sem evidência','metodo_reranker':'sem evidência'}
            saida.append({**requisito,'evidencia':melhor['trecho'],'score_recuperacao':melhor.get('score_recuperacao',0.0),'score_reranker':melhor.get('score_reranker',0.0),'metodo':melhor.get('metodo'),'metodo_reranker':melhor.get('metodo_reranker'),'top_evidencias':reranqueados})
        fortes=sum(float(e.get('score_reranker',0))>=0.6 for e in saida)
        return ResultadoAgente(
            agente=self.nome,resumo=f'Evidências recuperadas para {len(saida)} requisitos; {fortes} com forte aderência.',
            dados={'evidencias':saida,'status_motor':self.motor.status},confianca=round(fortes/len(saida),2) if saida else 0.0,
            tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
