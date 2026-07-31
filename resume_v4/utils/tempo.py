from __future__ import annotations
import time
from contextlib import contextmanager
from typing import Any, Iterator

@contextmanager
def medir(agente: str) -> Iterator[dict[str, Any]]:
    inicio=time.perf_counter()
    registro={"agente":agente,"status":"executando","resumo":"","alertas":[]}
    try:
        yield registro
        registro["status"]="concluido"
    except Exception as erro:
        registro["status"]="falhou"; registro["alertas"].append(str(erro)); raise
    finally:
        registro["tempo_ms"]=round((time.perf_counter()-inicio)*1000,2)
