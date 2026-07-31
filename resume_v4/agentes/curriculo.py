from __future__ import annotations
import re, time
from resume_v4.models import ResultadoAgente
from resume_v4.services.catalogo import CatalogoCompetencias
from resume_v4.utils.texto import normalizar, unidades

MARCADORES_FORMACAO=['universidade','faculdade','bacharel','graduação','graduacao','curso','degree','university','college','student']
MARCADORES_EXPERIENCIA=['experiência','experiencia','estágio','estagio','trabalhei','atuei','desenvolvi','implementei','criei','projeto','research','experience','developed','built','implemented']
MARCADORES_PROJETO=['projeto','project','desenvolvi','developed','construí','construi','built','implementei','implemented']

class AgenteCurriculo:
    nome='Agente de Currículo'
    def __init__(self,catalogo: CatalogoCompetencias | None=None) -> None:
        self.catalogo=catalogo or CatalogoCompetencias()

    def executar(self,texto_original: str,texto_anonimizado: str) -> ResultadoAgente:
        inicio=time.perf_counter(); linhas=[l.strip() for l in texto_original.splitlines() if l.strip()]
        candidato=linhas[0] if linhas and len(linhas[0].split())<=6 else 'Candidato não identificado'
        trechos=unidades(texto_anonimizado)
        competencias=self.catalogo.detectar(texto_anonimizado)
        formacao=[t for t in trechos if any(m in normalizar(t) for m in MARCADORES_FORMACAO)][:8]
        experiencia=[t for t in trechos if any(m in normalizar(t) for m in MARCADORES_EXPERIENCIA)][:15]
        projetos=[t for t in trechos if any(m in normalizar(t) for m in MARCADORES_PROJETO)][:12]
        anos=[]
        for match in re.finditer(r'\b(\d{1,2})\s*(?:anos?|years?)\b',normalizar(texto_anonimizado)):
            anos.append(int(match.group(1)))
        alertas=[]
        if len(competencias)<3: alertas.append('Poucas competências foram reconhecidas no currículo.')
        if not experiencia and not projetos: alertas.append('Não foram encontradas evidências claras de experiência ou projetos.')
        confianca=min(0.98,0.45+0.03*min(len(competencias),10)+0.01*min(len(trechos),20))
        return ResultadoAgente(
            agente=self.nome,
            resumo=f'{len(competencias)} competências e {len(experiencia)+len(projetos)} evidências profissionais identificadas.',
            dados={'candidato':candidato,'competencias':competencias,'formacao':formacao,'experiencia':experiencia,'projetos':projetos,'trechos':trechos,'anos_mencionados':anos},
            alertas=alertas,confianca=round(confianca,2),tempo_ms=round((time.perf_counter()-inicio)*1000,2),
        )
