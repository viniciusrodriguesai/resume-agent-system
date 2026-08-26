from __future__ import annotations

import re

from resume_ai.domain.models import Skill
from resume_ai.utils.text import exact_phrase, normalize

_COORDINATED_CONCEPT_RE = re.compile(
    r"\s*(?:,|;|\be\b|\band\b|\bou\b|\bor\b)\s*"
)
_REQUIREMENT_PREFIX_RE = re.compile(
    r"^(?:(?:experiencia|conhecimento|dominio|familiaridade|vivencia)"
    r"(?:\s+(?:com|em|de))?|(?:experience|knowledge|familiarity)"
    r"(?:\s+(?:with|in|of))?)\s+"
)

SKILLS: dict[str, tuple[str, list[str]]] = {
    "Python": ("programação", ["python"]),
    "SQL": ("banco de dados", ["sql", "structured query language"]),
    "Pandas": ("dados e IA", ["pandas"]),
    "NumPy": ("dados e IA", ["numpy"]),
    "Scikit-learn": ("dados e IA", ["scikit-learn", "sklearn"]),
    "PyTorch": ("dados e IA", ["pytorch"]),
    "TensorFlow": ("dados e IA", ["tensorflow"]),
    "Machine Learning": ("dados e IA", ["machine learning", "aprendizado de máquina", "aprendizado de maquina"]),
    "Estatística": ("dados e IA", ["estatística", "estatistica", "statistics"]),
    "Análise de dados": ("dados e IA", ["análise de dados", "analise de dados", "data analysis"]),
    "Power BI": ("visualização", ["power bi", "powerbi"]),
    "Tableau": ("visualização", ["tableau"]),
    "Matplotlib": ("visualização", ["matplotlib"]),
    "Plotly": ("visualização", ["plotly"]),
    "Git": ("ferramentas", ["git"]),
    "GitHub": ("ferramentas", ["github"]),
    "Docker": ("devops", ["docker", "container"]),
    "Linux": ("devops", ["linux"]),
    "AWS": ("nuvem", ["aws", "amazon web services"]),
    "Azure": ("nuvem", ["azure"]),
    "GCP": ("nuvem", ["gcp", "google cloud"]),
    "FastAPI": ("backend", ["fastapi"]),
    "REST API": ("backend", ["rest api", "api rest", "apis rest", "serviços web", "servicos web"]),
    "PostgreSQL": ("banco de dados", ["postgresql", "postgres"]),
    "MySQL": ("banco de dados", ["mysql"]),
    "SQLite": ("banco de dados", ["sqlite"]),
    "Comunicação": ("comportamental", ["comunicação", "comunicacao", "communication"]),
    "Trabalho em equipe": ("comportamental", ["trabalho em equipe", "teamwork", "colaboração", "colaboracao"]),
    "Resolução de problemas": ("comportamental", ["resolução de problemas", "resolucao de problemas", "problem solving"]),
    "Inglês": ("idiomas", ["inglês", "ingles", "english"]),
}


def detect_skills(text: str) -> list[Skill]:
    found: list[Skill] = []
    normalized = normalize(text)
    for name, (category, aliases) in SKILLS.items():
        if any(exact_phrase(normalized, alias) for alias in aliases):
            found.append(Skill(name=name, category=category, aliases=aliases))
    return found


def aliases_for(text: str) -> list[str]:
    normalized = normalize(text)
    result: list[str] = []
    for name, (_, aliases) in SKILLS.items():
        if exact_phrase(normalized, name) or any(exact_phrase(normalized, alias) for alias in aliases):
            result.extend([name, *aliases])
    return list(dict.fromkeys(result))


def concept_alias_groups(text: str) -> list[list[str]]:
    """Retorna um grupo de sinônimos por competência citada no requisito.

    Isso impede que um requisito com Pandas, NumPy e Scikit-learn seja considerado
    totalmente atendido só porque um dos três termos apareceu no currículo.
    """
    normalized = normalize(text)
    groups: list[list[str]] = []
    for name, (_, aliases) in SKILLS.items():
        values = [name, *aliases]
        if any(exact_phrase(normalized, value) for value in values):
            groups.append(list(dict.fromkeys(values)))

    coordinated_text = normalize(re.sub(r"[,;]", " and ", text))
    coordinated_parts = _COORDINATED_CONCEPT_RE.split(coordinated_text)
    if len(coordinated_parts) > 1:
        for part in coordinated_parts:
            literal = _REQUIREMENT_PREFIX_RE.sub("", part).strip()
            if not literal or len(literal.split()) > 6:
                continue
            if any(
                exact_phrase(part, alias)
                for group in groups
                for alias in group
            ):
                continue
            groups.append([literal])
    return groups


def category_for(text: str) -> str:
    normalized = normalize(text)
    for name, (category, aliases) in SKILLS.items():
        if exact_phrase(normalized, name) or any(exact_phrase(normalized, alias) for alias in aliases):
            return category
    if any(word in normalized for word in ("experiencia", "anos", "estagio")):
        return "experiência"
    if any(word in normalized for word in ("graduacao", "bacharel", "curso", "universidade")):
        return "formação"
    return "outros"
