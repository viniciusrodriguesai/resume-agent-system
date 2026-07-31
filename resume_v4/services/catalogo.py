from __future__ import annotations
import csv, sqlite3
from typing import Any
from rapidfuzz import fuzz, process
from resume_v4.config import ROOT, Config
from resume_v4.utils.texto import contem_frase, normalizar

class CatalogoCompetencias:
    def __init__(self, config: Config | None = None) -> None:
        self.config=config or Config(); self.config.preparar()
        self.amostra=ROOT/'data'/'esco_amostra_pt.csv'
        self.competencias=self._carregar(); self._nlp=None; self._por_id={item['id']:item for item in self.competencias}

    def _carregar(self) -> list[dict[str, Any]]:
        itens=[]
        if self.config.banco_esco.exists():
            try:
                with sqlite3.connect(self.config.banco_esco) as con:
                    rows=con.execute('SELECT id, rotulo, categoria, aliases FROM competencias').fetchall()
                for ident,rotulo,categoria,aliases in rows:
                    itens.append({'id':ident,'rotulo':rotulo,'categoria':categoria,'aliases':(aliases or '').split('|')})
                if itens: return itens
            except sqlite3.Error:
                pass
        with self.amostra.open(encoding='utf-8-sig',newline='') as arq:
            for linha in csv.DictReader(arq):
                itens.append({'id':linha['id'],'rotulo':linha['rotulo'],'categoria':linha['categoria'],'aliases':[a for a in linha['aliases'].split('|') if a]})
        return itens


    def _carregar_spacy(self):
        if self._nlp is not None:
            return self._nlp
        try:
            import spacy
            nlp=spacy.blank("xx")
            ruler=nlp.add_pipe("entity_ruler",config={"phrase_matcher_attr":"LOWER","overwrite_ents":True})
            patterns=[]
            for item in self.competencias:
                for frase in [item["rotulo"],*item["aliases"]]:
                    if frase.strip():
                        patterns.append({"label":"COMPETENCIA","pattern":frase,"id":item["id"]})
            ruler.add_patterns(patterns)
            self._nlp=nlp
        except Exception:
            self._nlp=False
        return self._nlp if self._nlp is not False else None

    def detectar(self, texto: str) -> list[dict[str, Any]]:
        nlp=self._carregar_spacy()
        if nlp is not None:
            agrupados={}
            for entidade in nlp(texto).ents:
                item=self._por_id.get(entidade.ent_id_)
                if not item:
                    continue
                agrupados.setdefault(item["id"],{**item,"evidencias_alias":[]})
                agrupados[item["id"]]["evidencias_alias"].append(entidade.text)
            if agrupados:
                for item in agrupados.values():
                    item["evidencias_alias"]=sorted(set(item["evidencias_alias"]))
                return list(agrupados.values())
        encontrados=[]
        for item in self.competencias:
            evidencias=[]
            for alias in [item['rotulo'],*item['aliases']]:
                if contem_frase(texto,alias): evidencias.append(alias)
            if evidencias:
                encontrados.append({**item,'evidencias_alias':sorted(set(evidencias))})
        return encontrados

    def aproximar(self, termo: str, limite: int = 5, corte: float = 70) -> list[dict[str, Any]]:
        escolhas={i:item['rotulo'] for i,item in enumerate(self.competencias)}
        resultados=process.extract(normalizar(termo), escolhas, scorer=fuzz.WRatio, limit=limite, score_cutoff=corte, processor=normalizar)
        return [{**self.competencias[indice],'similaridade_fuzzy':round(float(score)/100,3)} for _,score,indice in resultados]
