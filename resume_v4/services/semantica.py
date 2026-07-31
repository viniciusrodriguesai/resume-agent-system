from __future__ import annotations
from typing import Any
import math
import numpy as np
from rapidfuzz.fuzz import WRatio
from resume_v4.config import Config
from resume_v4.utils.texto import normalizar, similaridade_tfidf, contem_frase

class MotorSemantico:
    def __init__(self, config: Config | None = None) -> None:
        self.config=config or Config(); self._modelo=None; self._reranker=None

    @property
    def status(self) -> dict[str, Any]:
        return {
            'embeddings_carregados':self._modelo is not None,
            'reranker_carregado':self._reranker is not None,
            'modelo_embeddings':self.config.modelo_embeddings,
            'modelo_reranker':self.config.modelo_reranker,
        }

    def _carregar_embeddings(self):
        if self._modelo is not None: return self._modelo
        if not self.config.usar_embeddings: return None
        try:
            from sentence_transformers import SentenceTransformer
            self._modelo=SentenceTransformer(self.config.modelo_embeddings)
        except Exception:
            self._modelo=None
        return self._modelo

    def _carregar_reranker(self):
        if self._reranker is not None: return self._reranker
        if not self.config.usar_reranker: return None
        try:
            from sentence_transformers import CrossEncoder
            self._reranker=CrossEncoder(self.config.modelo_reranker)
        except Exception:
            self._reranker=None
        return self._reranker

    def recuperar(self, consulta: str, trechos: list[str], top_k: int | None = None) -> list[dict[str, Any]]:
        top_k=top_k or self.config.top_k
        if not trechos: return []
        modelo=self._carregar_embeddings()
        if modelo is not None:
            try:
                embeddings=modelo.encode([consulta,*trechos],normalize_embeddings=True,show_progress_bar=False)
                scores=np.dot(embeddings[1:],embeddings[0])
                ordem=np.argsort(-scores)[:top_k]
                return [
                    {'trecho':trechos[int(i)],'score_recuperacao':round(float(scores[int(i)]),4),'metodo':'BGE-M3'}
                    for i in ordem
                ]
            except Exception:
                pass
        avaliados=[]
        aliases=[parte.strip() for parte in consulta.split('|') if parte.strip()]
        for trecho in trechos:
            exato=any(contem_frase(trecho,alias) for alias in aliases)
            tfidf=similaridade_tfidf(consulta,trecho)
            fuzzy=WRatio(normalizar(consulta),normalizar(trecho))/100
            score=1.0 if exato else 0.65*tfidf+0.35*fuzzy
            avaliados.append({
                'trecho':trecho,
                'score_recuperacao':round(score,4),
                'metodo':'Alias exato' if exato else 'TF-IDF + RapidFuzz',
            })
        return sorted(avaliados,key=lambda x:x['score_recuperacao'],reverse=True)[:top_k]

    def reranquear(self, consulta: str, candidatos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not candidatos: return []
        reranker=self._carregar_reranker()
        if reranker is not None:
            try:
                pares=[[consulta,c['trecho']] for c in candidatos]
                scores=reranker.predict(pares,show_progress_bar=False)
                for candidato,score in zip(candidatos,scores):
                    valor=float(score); normalizado=valor if 0.0 <= valor <= 1.0 else 1.0/(1.0+math.exp(-valor)); candidato['score_reranker']=round(normalizado,4)
                    candidato['metodo_reranker']='BGE Reranker v2 M3'
                return sorted(candidatos,key=lambda x:x['score_reranker'],reverse=True)
            except Exception:
                pass
        for candidato in candidatos:
            candidato['score_reranker']=candidato['score_recuperacao']
            candidato['metodo_reranker']='Pontuação de recuperação'
        return sorted(candidatos,key=lambda x:x['score_reranker'],reverse=True)
