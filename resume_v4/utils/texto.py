from __future__ import annotations
import math, re, unicodedata
from collections import Counter
from typing import Iterable

STOPWORDS = {"a","as","ao","aos","com","da","das","de","do","dos","e","em","entre","é","o","os","ou","para","por","que","se","um","uma","the","and","of","to","in","for","with","is","are"}

def normalizar(texto: str) -> str:
    valor = unicodedata.normalize("NFKD", texto or "")
    valor = "".join(c for c in valor if not unicodedata.combining(c)).lower()
    valor = re.sub(r"[^a-z0-9+#./\-\s]", " ", valor)
    return re.sub(r"\s+", " ", valor).strip()

def unidades(texto: str, minimo: int = 3) -> list[str]:
    saida: list[str] = []
    for linha in (texto or "").splitlines():
        linha = re.sub(r"^[\s•*\-–—\d.)]+", "", linha).strip()
        if not linha:
            continue
        for parte in re.split(r"(?<=[.!?;:])\s+", linha):
            parte = parte.strip()
            if len(parte) >= minimo:
                saida.append(parte)
    return saida

def tokens(texto: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#]+", normalizar(texto)) if len(t)>1 and t not in STOPWORDS]

def similaridade_tfidf(a: str, b: str) -> float:
    docs=[tokens(a),tokens(b)]
    df=Counter()
    for doc in docs: df.update(set(doc))
    idf={t: math.log(3/(1+f))+1 for t,f in df.items()}
    vetores=[]
    for doc in docs:
        cont=Counter(doc); total=max(len(doc),1)
        vetores.append({t:(c/total)*idf[t] for t,c in cont.items()})
    va,vb=vetores
    if not va or not vb: return 0.0
    prod=sum(v*vb.get(t,0.0) for t,v in va.items())
    na=math.sqrt(sum(v*v for v in va.values())); nb=math.sqrt(sum(v*v for v in vb.values()))
    return prod/(na*nb) if na and nb else 0.0

def contem_frase(texto: str, frase: str) -> bool:
    f=normalizar(frase)
    return bool(f and f" {f} " in f" {normalizar(texto)} ")

def contem_marcador(texto: str, marcadores: Iterable[str]) -> bool:
    t=normalizar(texto)
    return any(normalizar(m) in t for m in marcadores)
