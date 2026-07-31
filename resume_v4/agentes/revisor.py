from __future__ import annotations
import time
from resume_v4.models import ResultadoAgente

class AgenteRevisor:
    nome='Agente Revisor e Auditor'
    def executar(self,pontuacao: dict,revisoes: int,max_revisoes: int) -> ResultadoAgente:
        inicio=time.perf_counter(); problemas=[]; borderline=[]
        limiar_parcial=float(pontuacao.get('limiares',{}).get('parcial',0.35))
        for item in pontuacao.get('resultados',[]):
            score=float(item.get('score_final',0.0))
            if item.get('prioridade')=='obrigatorio' and item.get('status')=='ausente' and score>=max(0.18,limiar_parcial-0.12):
                borderline.append(item.get('id'))
        if borderline: problemas.append('Há requisitos obrigatórios com evidências próximas do limiar e que merecem nova verificação.')
        if pontuacao.get('ausentes_obrigatorios',0) and pontuacao.get('score_geral',0)>72:
            problemas.append('A pontuação está alta demais para a quantidade de requisitos obrigatórios ausentes.')
        if not pontuacao.get('resultados'): problemas.append('Nenhum requisito foi analisado.')
        solicitar=bool(problemas and revisoes<max_revisoes)
        decisao='revisar' if solicitar else 'aprovado'
        texto=(
            'O revisor solicitou uma segunda passagem, ampliando a busca por evidências próximas do limiar.'
            if solicitar else
            f"Análise aprovada: compatibilidade {str(pontuacao.get('nivel','Baixa')).lower()} de {pontuacao.get('score_geral',0)}%. O resultado deve apoiar, e não substituir, a avaliação humana."
        )
        return ResultadoAgente(
            agente=self.nome,resumo=f'Decisão da auditoria: {decisao}.',
            dados={'decisao':decisao,'solicitar_revisao':solicitar,'problemas':problemas,'ids_borderline':borderline,'texto_final':texto},
            alertas=problemas,confianca=0.95 if not solicitar else 0.8,
            tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
