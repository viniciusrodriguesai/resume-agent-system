from __future__ import annotations
import json,time
from resume_v4.models import ResultadoAgente

class AgenteRelatorio:
    nome='Agente de Relatório'
    def executar(self,analise_id: str,perfil_curriculo: dict,perfil_vaga: dict,pontuacao: dict,revisao: dict,recomendacoes: list[dict],privacidade: dict,status_motor: dict) -> ResultadoAgente:
        inicio=time.perf_counter(); linhas=[
            '# Relatório de Compatibilidade Currículo–Vaga','',
            f"**ID da análise:** {analise_id}",
            f"**Candidato:** {perfil_curriculo.get('candidato','Não identificado')}",
            f"**Vaga:** {perfil_vaga.get('titulo','Não identificada')}",
            f"**Compatibilidade geral:** {pontuacao.get('score_geral',0)}%",
            f"**Nível:** {pontuacao.get('nivel','Baixa')}",
            f"**Decisão do revisor:** {revisao.get('decisao','desconhecida')}",'',
            '## Pontuação por categoria','',
        ]
        for categoria,valor in pontuacao.get('scores_categoria',{}).items(): linhas.append(f'- **{categoria}:** {valor}%')
        linhas.extend(['','## Requisitos e evidências',''])
        for item in pontuacao.get('resultados',[]):
            linhas.extend([
                f"### {item.get('texto')}",
                f"- Prioridade: {item.get('prioridade')}",
                f"- Status: {item.get('status')}",
                f"- Pontuação semântica: {float(item.get('score_final',0)):.3f}",
                f"- Evidência: {item.get('evidencia') or 'Nenhuma evidência identificada.'}",
                f"- Método: {item.get('metodo')} / {item.get('metodo_reranker')}",'',
            ])
        linhas.extend(['## Recomendações',''])
        for item in recomendacoes: linhas.append(f"- **{item.get('prioridade')} — {item.get('categoria')}:** {item.get('acao')}")
        linhas.extend(['','## Privacidade','',f"Método: {privacidade.get('metodo')}. Foram detectadas {len(privacidade.get('entidades',[]))} entidades pessoais.",'','## Motor de IA','',f"Embeddings: {status_motor.get('modelo_embeddings')}; reranker: {status_motor.get('modelo_reranker')}.",'','## Revisão final','',str(revisao.get('texto_final','')),'',
        '> Este sistema oferece apoio à análise técnica. Ele não deve ser usado como única base para decisões de contratação.'])
        dados={'analise_id':analise_id,'curriculo':perfil_curriculo,'vaga':perfil_vaga,'pontuacao':pontuacao,'revisao':revisao,'recomendacoes':recomendacoes,'privacidade':privacidade,'motor':status_motor}
        return ResultadoAgente(
            agente=self.nome,resumo='Relatórios Markdown e JSON gerados.',
            dados={'markdown':'\n'.join(linhas),'json':json.dumps(dados,ensure_ascii=False,indent=2)},confianca=1.0,
            tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
