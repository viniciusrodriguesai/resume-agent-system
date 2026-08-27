from __future__ import annotations


def runtime_status_label(*, enabled: bool, loaded: bool) -> str:
    if not enabled:
        return "Desativado"
    if loaded:
        return "Carregado"
    return "Habilitado · fallback"


def backend_error_reason(error: object) -> str:
    value = str(error or "")
    error_type = value.rsplit(":", 1)[-1]
    if error_type in {"ModuleNotFoundError", "ImportError"}:
        return "dependência opcional indisponível"
    if error_type == "MemoryError":
        return "memória insuficiente para carregar o modelo"
    return "modelo indisponível nesta execução"
