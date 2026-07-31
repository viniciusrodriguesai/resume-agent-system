from __future__ import annotations
from typing import Dict, List

SKILL_ONTOLOGY: Dict[str, Dict[str, List[str]]] = {
    "programming": {
        "python": ["python", "python3"],
        "java": ["java"],
        "javascript": ["javascript", "js"],
        "typescript": ["typescript", "ts"],
        "c++": ["c++", "cpp"],
        "c#": ["c#", "c sharp"],
        "r": ["r language", "r programming"],
        "sql": ["sql", "structured query language"],
    },
    "data_and_ai": {
        "machine learning": ["machine learning", "predictive modeling", "predictive analytics", "ml models"],
        "deep learning": ["deep learning", "neural networks", "neural network"],
        "artificial intelligence": ["artificial intelligence", "ai systems"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "scikit-learn": ["scikit-learn", "sklearn"],
        "pytorch": ["pytorch", "torch"],
        "tensorflow": ["tensorflow", "keras"],
        "statistics": ["statistics", "statistical analysis"],
        "data analysis": ["data analysis", "data analytics", "analyze data"],
        "data visualization": ["data visualization", "visual analytics", "dashboards", "dashboard development"],
        "power bi": ["power bi", "powerbi", "business intelligence dashboards"],
        "tableau": ["tableau"],
        "matplotlib": ["matplotlib"],
    },
    "backend_and_databases": {
        "api": ["api", "apis", "application programming interface"],
        "rest api": ["rest api", "restful api", "web services", "rest services"],
        "fastapi": ["fastapi"],
        "flask": ["flask"],
        "django": ["django"],
        "postgresql": ["postgresql", "postgres"],
        "mysql": ["mysql"],
        "mongodb": ["mongodb", "mongo db"],
        "database": ["database", "databases", "relational database"],
    },
    "cloud_and_devops": {
        "aws": ["aws", "amazon web services"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud platform", "google cloud"],
        "docker": ["docker", "containers", "containerization"],
        "kubernetes": ["kubernetes", "k8s"],
        "linux": ["linux"],
        "git": ["git", "version control"],
        "github": ["github"],
        "ci/cd": ["ci/cd", "continuous integration", "continuous delivery"],
    },
    "soft_skills": {
        "communication": ["communication", "communicate", "presentation skills"],
        "teamwork": ["teamwork", "team work", "collaboration", "worked with a team"],
        "leadership": ["leadership", "led a team", "team leader"],
        "problem solving": ["problem solving", "problem-solving", "solve problems"],
        "organization": ["organization", "organized", "time management"],
        "proactivity": ["proactivity", "proactive", "initiative"],
        "fast learning": ["fast learning", "quick learner", "learning agility"],
    },
    "languages": {
        "english": ["english", "english communication"],
        "portuguese": ["portuguese"],
        "spanish": ["spanish"],
        "german": ["german"],
        "french": ["french"],
    },
}

SECTION_ALIASES = {
    "education": ["education", "academic background", "university", "college", "bachelor", "master", "degree", "graduation", "student"],
    "experience": ["experience", "employment", "work history", "internship", "research", "assistant", "volunteer"],
    "projects": ["projects", "project", "portfolio", "developed", "built", "implemented"],
}
REQUIRED_MARKERS = ["required", "mandatory", "must", "essential", "minimum", "need", "needs", "proficiency", "experience with", "knowledge of"]
DESIRABLE_MARKERS = ["preferred", "desirable", "nice to have", "plus", "bonus", "advantage", "optional"]
RESPONSIBILITY_MARKERS = ["responsibilities", "you will", "will be responsible", "support", "develop", "build", "analyze", "create", "design", "maintain"]
