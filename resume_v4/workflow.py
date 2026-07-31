from __future__ import annotations
import sqlite3, uuid
from typing import Any, TypedDict
from resume_v4.agentes import (
    AgenteCurriculo,AgenteVaga,AgenteEvidencias,AgentePontuacao,
    AgentePrivacidade,AgenteRevisor,AgenteRecomendacoes,AgenteRelatorio,
)
from resume_v4.config import Config
from resume_v4.services import CatalogoCompetencias, MotorSemantico, Historico

class EstadoGrafo(TypedDict,total=False):
    analise_id: str
    curriculo_original: str
    vaga_original: str
    curriculo_anonimizado: str
    perfil_curriculo: dict[str,Any]
    perfil_vaga: dict[str,Any]
    evidencias: list[dict[str,Any]]
    pontuacao: dict[str,Any]
    revisao: dict[str,Any]
    recomendacoes: list[dict[str,Any]]
    relatorio_markdown: str
    relatorio_json: str
    privacidade: dict[str,Any]
    revisoes: int
    top_k: int
    rigor: str
    rastreio: list[dict[str,Any]]
    status_motor: dict[str,Any]

class SistemaV4:
    def __init__(self,config: Config | None=None) -> None:
        self.config=config or Config(); self.config.preparar()
        catalogo=CatalogoCompetencias(self.config); motor=MotorSemantico(self.config)
        self.privacidade=AgentePrivacidade()
        self.curriculo=AgenteCurriculo(catalogo)
        self.vaga=AgenteVaga(catalogo)
        self.evidencias=AgenteEvidencias(motor)
        self.pontuacao=AgentePontuacao()
        self.revisor=AgenteRevisor()
        self.recomendador=AgenteRecomendacoes()
        self.relatorio=AgenteRelatorio()
        self.historico=Historico(self.config)
        self._motor=motor
        self._grafo=self._construir_grafo()

    @staticmethod
    def _registro(resultado) -> dict[str,Any]:
        return {
            'agente':resultado.agente,'resumo':resultado.resumo,
            'confianca':resultado.confianca,'tempo_ms':resultado.tempo_ms,
            'alertas':resultado.alertas,
        }

    def _no_privacidade(self,state: EstadoGrafo) -> dict:
        r=self.privacidade.executar(state['curriculo_original'])
        return {'curriculo_anonimizado':r.dados['texto'],'privacidade':r.dados,'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_curriculo(self,state: EstadoGrafo) -> dict:
        r=self.curriculo.executar(state['curriculo_original'],state['curriculo_anonimizado'])
        return {'perfil_curriculo':r.dados,'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_vaga(self,state: EstadoGrafo) -> dict:
        r=self.vaga.executar(state['vaga_original'])
        return {'perfil_vaga':r.dados,'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_evidencias(self,state: EstadoGrafo) -> dict:
        r=self.evidencias.executar(state['perfil_curriculo'],state['perfil_vaga'],top_k=state.get('top_k',self.config.top_k))
        return {'evidencias':r.dados['evidencias'],'status_motor':r.dados['status_motor'],'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_pontuacao(self,state: EstadoGrafo) -> dict:
        r=self.pontuacao.executar(state['evidencias'],state.get('rigor','Equilibrado'))
        return {'pontuacao':r.dados,'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_revisao(self,state: EstadoGrafo) -> dict:
        r=self.revisor.executar(state['pontuacao'],state.get('revisoes',0),self.config.max_revisoes)
        return {'revisao':r.dados,'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_preparar_revisao(self,state: EstadoGrafo) -> dict:
        return {'revisoes':state.get('revisoes',0)+1,'top_k':state.get('top_k',self.config.top_k)+3}

    def _no_recomendacoes(self,state: EstadoGrafo) -> dict:
        r=self.recomendador.executar(state['perfil_curriculo'],state['pontuacao'])
        return {'recomendacoes':r.dados['recomendacoes'],'rastreio':state.get('rastreio',[])+[self._registro(r)]}

    def _no_relatorio(self,state: EstadoGrafo) -> dict:
        r=self.relatorio.executar(
            state['analise_id'],state['perfil_curriculo'],state['perfil_vaga'],
            state['pontuacao'],state['revisao'],state['recomendacoes'],
            state['privacidade'],state.get('status_motor',self._motor.status),
        )
        retorno={'relatorio_markdown':r.dados['markdown'],'relatorio_json':r.dados['json'],'rastreio':state.get('rastreio',[])+[self._registro(r)]}
        self.historico.salvar(
            state['analise_id'],state['perfil_curriculo'].get('candidato',''),
            state['perfil_vaga'].get('titulo',''),int(state['pontuacao'].get('score_geral',0)),
            str(state['pontuacao'].get('nivel','')),{'pontuacao':state['pontuacao'],'revisao':state['revisao']},
        )
        return retorno

    @staticmethod
    def _rota_revisao(state: EstadoGrafo) -> str:
        return 'revisar' if state.get('revisao',{}).get('solicitar_revisao') else 'seguir'

    def _construir_grafo(self):
        try:
            from langgraph.graph import StateGraph, START, END
            builder=StateGraph(EstadoGrafo)
            builder.add_node('privacidade',self._no_privacidade)
            builder.add_node('curriculo',self._no_curriculo)
            builder.add_node('vaga',self._no_vaga)
            builder.add_node('evidencias',self._no_evidencias)
            builder.add_node('pontuacao',self._no_pontuacao)
            builder.add_node('revisao',self._no_revisao)
            builder.add_node('preparar_revisao',self._no_preparar_revisao)
            builder.add_node('recomendacoes',self._no_recomendacoes)
            builder.add_node('relatorio',self._no_relatorio)
            builder.add_edge(START,'privacidade'); builder.add_edge('privacidade','curriculo')
            builder.add_edge('curriculo','vaga'); builder.add_edge('vaga','evidencias')
            builder.add_edge('evidencias','pontuacao'); builder.add_edge('pontuacao','revisao')
            builder.add_conditional_edges('revisao',self._rota_revisao,{'revisar':'preparar_revisao','seguir':'recomendacoes'})
            builder.add_edge('preparar_revisao','evidencias'); builder.add_edge('recomendacoes','relatorio'); builder.add_edge('relatorio',END)
            # Checkpoint SQLite quando o pacote correspondente estiver disponível.
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver
                conexao=sqlite3.connect(self.config.banco_checkpoints,check_same_thread=False)
                self._conexao_checkpoint=conexao
                return builder.compile(checkpointer=SqliteSaver(conexao))
            except Exception:
                return builder.compile()
        except Exception:
            return None

    def analisar(self,curriculo: str,vaga: str,rigor: str='Equilibrado') -> dict[str,Any]:
        inicial: EstadoGrafo={
            'analise_id':str(uuid.uuid4()),'curriculo_original':curriculo,'vaga_original':vaga,
            'revisoes':0,'top_k':self.config.top_k,'rigor':rigor,'rastreio':[],
        }
        if self._grafo is not None:
            config={'configurable':{'thread_id':inicial['analise_id']}}
            return dict(self._grafo.invoke(inicial,config=config))
        # Fallback sem LangGraph, mantendo o mesmo fluxo e o ciclo de revisão.
        estado=dict(inicial)
        for no in [self._no_privacidade,self._no_curriculo,self._no_vaga,self._no_evidencias,self._no_pontuacao,self._no_revisao]: estado.update(no(estado))
        if estado['revisao'].get('solicitar_revisao'):
            estado.update(self._no_preparar_revisao(estado)); estado.update(self._no_evidencias(estado)); estado.update(self._no_pontuacao(estado)); estado.update(self._no_revisao(estado))
        estado.update(self._no_recomendacoes(estado)); estado.update(self._no_relatorio(estado))
        return estado
