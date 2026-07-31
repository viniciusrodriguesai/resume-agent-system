from __future__ import annotations

from resume_ai.domain.models import Skill
from resume_ai.utils.text import exact_phrase, normalize

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
        if normalize(name) in normalized or any(normalize(alias) in normalized for alias in aliases):
            result.extend([name, *aliases])
    return list(dict.fromkeys(result))


def category_for(text: str) -> str:
    normalized = normalize(text)
    for name, (category, aliases) in SKILLS.items():
        if normalize(name) in normalized or any(normalize(alias) in normalized for alias in aliases):
            return category
    if any(word in normalized for word in ("experiencia", "anos", "estagio")):
        return "experiência"
    if any(word in normalized for word in ("graduacao", "bacharel", "curso", "universidade")):
        return "formação"
    return "outros"
