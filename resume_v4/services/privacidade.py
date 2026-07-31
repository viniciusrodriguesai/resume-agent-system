from __future__ import annotations
import re
from typing import Any
from resume_v4.config import Config

PADROES={
    'EMAIL':r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+',
    'TELEFONE':r'(?:\+?\d{1,3}\s*)?(?:\(?\d{2,3}\)?\s*)?\d{4,5}[-\s]?\d{4}',
    'CPF':r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    'URL':r'https?://\S+|www\.\S+',
}

class ServicoPrivacidade:
    def __init__(self, config: Config | None = None) -> None:
        self.config=config or Config()

    def anonimizar(self, texto: str) -> dict[str, Any]:
        if self.config.usar_presidio:
            resultado=self._presidio(texto)
            if resultado: return resultado
        saida=texto; entidades=[]
        for tipo,padrao in PADROES.items():
            for match in list(re.finditer(padrao,saida,flags=re.I)):
                entidades.append({'tipo':tipo,'texto':match.group(0)})
            saida=re.sub(padrao,f'<{tipo}>',saida,flags=re.I)
        linhas=saida.splitlines()
        for i,linha in enumerate(linhas[:4]):
            valor=linha.strip()
            if valor and len(valor.split())<=6 and not re.search(r'[@\d:]',valor):
                entidades.append({'tipo':'NOME_CANDIDATO','texto':valor}); linhas[i]='<NOME_CANDIDATO>'; break
        return {'texto': '\n'.join(linhas),'entidades':entidades,'metodo':'Expressões regulares locais'}

    def _presidio(self, texto: str) -> dict[str, Any] | None:
        try:
            from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine
        except Exception:
            return None
        try:
            configuracao={'nlp_engine_name':'spacy','models':[{'lang_code':'en','model_name':'en_core_web_sm'}]}
            nlp_engine=NlpEngineProvider(nlp_configuration=configuracao).create_engine()
            analyzer=AnalyzerEngine(nlp_engine=nlp_engine,supported_languages=['en'])
            cpf=Pattern(name='cpf',regex=PADROES['CPF'],score=0.85)
            analyzer.registry.add_recognizer(PatternRecognizer(supported_entity='BR_CPF',patterns=[cpf]))
            resultados=analyzer.analyze(text=texto,language='en',entities=['PERSON','EMAIL_ADDRESS','PHONE_NUMBER','LOCATION','URL','BR_CPF'])
            anon=AnonymizerEngine().anonymize(text=texto,analyzer_results=resultados)
            entidades=[{'tipo':r.entity_type,'inicio':r.start,'fim':r.end,'score':round(float(r.score),3)} for r in resultados]
            texto_anonimo=anon.text
            linhas=texto_anonimo.splitlines()
            for i,linha in enumerate(linhas[:4]):
                valor=linha.strip()
                if valor and len(valor.split())<=6 and not re.search(r'[@\d:<>]',valor):
                    entidades.append({'tipo':'NOME_CANDIDATO','texto':valor}); linhas[i]='<NOME_CANDIDATO>'; break
            return {'texto':'\n'.join(linhas),'entidades':entidades,'metodo':'Microsoft Presidio + proteção de cabeçalho'}
        except Exception:
            return None
