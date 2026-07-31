from __future__ import annotations
import re, time
from resume_v4.models import ResultadoAgente
from resume_v4.services.catalogo import CatalogoCompetencias
from resume_v4.utils.texto import normalizar, unidades

OBRIGATORIOS=['obrigatório','obrigatorio','necessário','necessario','requerido','required','must','mandatory','essential','mínimo','minimo']
DESEJAVEIS=['desejável','desejavel','diferencial','preferencial','preferred','nice to have','plus','bonus','vantagem']
RESPONSABILIDADES=['responsabilidades','irá','ira','será responsável','sera responsavel','analisar','desenvolver','criar','construir','apoiar','colaborar','you will','responsible','develop','analyze','build','support']
FORMACAO=['graduação','graduacao','bacharel','superior','universidade','degree','bachelor','university','college']

class AgenteVaga:
    nome='Agente de Vaga'
    def __init__(self,catalogo: CatalogoCompetencias | None=None) -> None:
        self.catalogo=catalogo or CatalogoCompetencias()

    @staticmethod
    def prioridade(trecho: str) -> str:
        n=normalizar(trecho)
        if any(normalizar(m) in n for m in DESEJAVEIS): return 'desejavel'
        if any(normalizar(m) in n for m in OBRIGATORIOS): return 'obrigatorio'
        return 'neutro'

    def executar(self,texto: str) -> ResultadoAgente:
        inicio=time.perf_counter(); trechos=unidades(texto)
        titulo=next((l.strip() for l in texto.splitlines() if l.strip() and len(l.split())<=10),'Vaga não identificada')
        competencias=self.catalogo.detectar(texto); requisitos=[]
        for item in competencias:
            origem=next((t for t in trechos if any(normalizar(a) in normalizar(t) for a in [item['rotulo'],*item['aliases']])),item['rotulo'])
            requisitos.append({'id':item['id'],'texto':item['rotulo'],'prioridade':self.prioridade(origem),'categoria':item['categoria'],'tipo':'competencia','aliases':item['aliases'],'origem':origem})
        contador=0
        for trecho in trechos:
            n=normalizar(trecho)
            if any(normalizar(m) in n for m in RESPONSABILIDADES):
                contador+=1; requisitos.append({'id':f'resp-{contador}','texto':trecho,'prioridade':self.prioridade(trecho),'categoria':'experiencia','tipo':'responsabilidade','aliases':[],'origem':trecho})
        formacoes=[]
        for trecho in trechos:
            if any(normalizar(m) in normalizar(trecho) for m in FORMACAO):
                formacoes.append(trecho)
        for i,trecho in enumerate(formacoes[:4],1):
            requisitos.append({'id':f'formacao-{i}','texto':trecho,'prioridade':self.prioridade(trecho),'categoria':'formacao','tipo':'formacao','aliases':[],'origem':trecho})
        # remove duplicatas por id/texto
        unicos=[]; vistos=set()
        for r in requisitos:
            chave=(r['id'],normalizar(r['texto']))
            if chave not in vistos: vistos.add(chave); unicos.append(r)
        alertas=[]
        if not unicos: alertas.append('Nenhum requisito estruturado foi identificado.')
        if unicos and not any(r['prioridade']=='obrigatorio' for r in unicos): alertas.append('A vaga não marcou requisitos obrigatórios explicitamente.')
        return ResultadoAgente(
            agente=self.nome,resumo=f'{len(unicos)} requisitos estruturados para “{titulo}”.',
            dados={'titulo':titulo,'requisitos':unicos,'trechos':trechos},alertas=alertas,
            confianca=round(min(0.98,0.5+0.025*len(unicos)),2),tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
