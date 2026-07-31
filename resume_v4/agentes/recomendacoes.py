from __future__ import annotations
import time
from resume_v4.models import ResultadoAgente

class AgenteRecomendacoes:
    nome='Agente de Recomendações'
    def executar(self,perfil_curriculo: dict,pontuacao: dict) -> ResultadoAgente:
        inicio=time.perf_counter(); recomendacoes=[]
        resultados=pontuacao.get('resultados',[])
        for item in [r for r in resultados if r.get('prioridade')=='obrigatorio' and r.get('status')=='ausente'][:6]:
            recomendacoes.append({'prioridade':'Alta','categoria':'Lacuna obrigatória','acao':f"Desenvolva evidência real para “{item.get('texto')}”. Não inclua essa competência no currículo antes de estudá-la ou aplicá-la em um projeto."})
        for item in [r for r in resultados if r.get('prioridade')=='obrigatorio' and r.get('status')=='parcial'][:6]:
            recomendacoes.append({'prioridade':'Alta','categoria':'Evidência insuficiente','acao':f"Reescreva a experiência relacionada a “{item.get('texto')}” indicando ação, tecnologia utilizada e resultado mensurável."})
        for item in [r for r in resultados if r.get('prioridade')=='desejavel' and r.get('status')=='ausente'][:5]:
            recomendacoes.append({'prioridade':'Média','categoria':'Desenvolvimento','acao':f"Considere estudar ou praticar “{item.get('texto')}”, pois aparece como diferencial na vaga."})
        if not perfil_curriculo.get('projetos'):
            recomendacoes.append({'prioridade':'Média','categoria':'Portfólio','acao':'Inclua projetos com problema, dados utilizados, tecnologias, sua contribuição e resultados.'})
        if not perfil_curriculo.get('formacao'):
            recomendacoes.append({'prioridade':'Média','categoria':'Estrutura','acao':'Deixe a formação acadêmica claramente identificada no currículo.'})
        if not recomendacoes:
            recomendacoes.append({'prioridade':'Baixa','categoria':'Personalização','acao':'Adapte o resumo e os projetos para a vaga, mantendo somente informações verdadeiras.'})
        return ResultadoAgente(
            agente=self.nome,resumo=f'{len(recomendacoes)} recomendações priorizadas foram geradas.',
            dados={'recomendacoes':recomendacoes},confianca=0.93,
            tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
