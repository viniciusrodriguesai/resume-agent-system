from __future__ import annotations
import time
from collections import defaultdict
from resume_v4.models import ResultadoAgente

PESOS_PRIORIDADE={'obrigatorio':1.0,'desejavel':0.45,'neutro':0.2}
VALORES_STATUS={'atendido':1.0,'parcial':0.55,'ausente':0.0}
ROTULOS={'programacao':'Programação','dados_ia':'Dados e IA','banco_de_dados':'Banco de dados','visualizacao':'Visualização','devops':'DevOps','nuvem':'Nuvem','backend':'Backend','comportamental':'Competências comportamentais','idiomas':'Idiomas','experiencia':'Experiência','formacao':'Formação'}
LIMIARES={'Flexível':(0.50,0.28),'Equilibrado':(0.60,0.35),'Conservador':(0.70,0.43)}

class AgentePontuacao:
    nome='Agente de Pontuação Explicável'
    def executar(self,evidencias: list[dict],rigor: str='Equilibrado') -> ResultadoAgente:
        inicio=time.perf_counter(); atendido,parcial=LIMIARES.get(rigor,LIMIARES['Equilibrado'])
        total=ganho=0.0; totais=defaultdict(float); ganhos=defaultdict(float); resultados=[]
        obrigatorios=ausentes_obrigatorios=0
        for item in evidencias:
            score=float(item.get('score_reranker',0.0))
            status='atendido' if score>=atendido else 'parcial' if score>=parcial else 'ausente'
            peso=PESOS_PRIORIDADE.get(item.get('prioridade','neutro'),0.2); valor=VALORES_STATUS[status]
            categoria=item.get('categoria','outros'); total+=peso; ganho+=peso*valor; totais[categoria]+=peso; ganhos[categoria]+=peso*valor
            if item.get('prioridade')=='obrigatorio':
                obrigatorios+=1
                if status=='ausente': ausentes_obrigatorios+=1
            resultados.append({**item,'status':status,'score_final':round(score,4)})
        geral=round(100*ganho/total) if total else 0
        if obrigatorios and ausentes_obrigatorios:
            proporcao=ausentes_obrigatorios/obrigatorios
            if proporcao>=0.5: geral=min(geral,55)
            elif proporcao>=0.25: geral=min(geral,72)
        categorias={ROTULOS.get(c,c.title()):round(100*ganhos[c]/t) for c,t in totais.items() if t}
        nivel='Alta' if geral>=82 else 'Média' if geral>=62 else 'Baixa'
        contagens={s:sum(r['status']==s for r in resultados) for s in VALORES_STATUS}
        return ResultadoAgente(
            agente=self.nome,resumo=f'Compatibilidade {nivel.lower()}: {geral}%.',
            dados={'score_geral':geral,'nivel':nivel,'scores_categoria':categorias,'resultados':resultados,'contagens':contagens,'obrigatorios':obrigatorios,'ausentes_obrigatorios':ausentes_obrigatorios,'rigor':rigor,'limiares':{'atendido':atendido,'parcial':parcial}},
            confianca=round(sum(float(r['score_final']) for r in resultados)/len(resultados),2) if resultados else 0.0,
            tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
