import re
from typing import Dict, Iterable, List, Set


SKILL_GROUPS: Dict[str, List[str]] = {
    "programming": [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "r",
        "sql",
    ],
    "data_and_ai": [
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "ai",
        "pandas",
        "numpy",
        "scikit-learn",
        "pytorch",
        "tensorflow",
        "regression",
        "classification",
        "statistics",
        "power bi",
        "tableau",
        "matplotlib",
        "seaborn",
    ],
    "backend": [
        "api",
        "rest",
        "fastapi",
        "flask",
        "django",
        "node",
        "postgresql",
        "mysql",
        "mongodb",
    ],
    "cloud_and_devops": [
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "linux",
        "git",
        "github",
        "ci/cd",
    ],
    "soft_skills": [
        "communication",
        "leadership",
        "teamwork",
        "problem solving",
        "organization",
        "proactivity",
        "collaboration",
        "fast learning",
    ],
    "languages": [
        "english",
        "spanish",
        "german",
        "french",
        "portuguese",
    ],
}

ALL_SKILLS = sorted({skill for skills in SKILL_GROUPS.values() for skill in skills})

HIGH_PRIORITY_WORDS = [
    "mandatory",
    "required",
    "requirement",
    "requirements",
    "must",
    "necessary",
    "needs",
    "experience with",
    "knowledge of",
    "proficiency in",
]

DESIRABLE_WORDS = [
    "desirable",
    "preferred",
    "nice to have",
    "plus",
    "advantage",
    "bonus",
]


def normalize_text(text: str) -> str:
    """Normalize whitespace and casing for keyword comparison."""
    return re.sub(r"\s+", " ", text or "").strip().lower()


def split_lines(text: str) -> List[str]:
    """Return non-empty, stripped lines."""
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def find_skills(text: str, vocabulary: Iterable[str] = ALL_SKILLS) -> Set[str]:
    """Find known skills using boundary-aware keyword matching."""
    normalized = normalize_text(text)
    found = set()
    for skill in vocabulary:
        pattern = r"(?<![\w+])" + re.escape(skill.lower()) + r"(?![\w+])"
        if re.search(pattern, normalized):
            found.add(skill)
    return found


def extract_contact(text: str) -> Dict[str, str]:
    """Extract an email address and a broadly formatted phone number."""
    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text or "")
    phone_match = re.search(
        r"(?:\+?\d{1,3}\s*)?(?:\(?\d{2,3}\)?\s*)?\d{4,5}[-\s]?\d{4}",
        text or "",
    )
    return {
        "email": email_match.group(0) if email_match else "not identified",
        "phone": phone_match.group(0) if phone_match else "not identified",
    }


def extract_relevant_lines(
    text: str,
    keywords: Iterable[str],
    max_items: int = 6,
) -> List[str]:
    """Select lines containing at least one relevant keyword."""
    lines = split_lines(text)
    selected: List[str] = []
    lowered_keywords = [keyword.lower() for keyword in keywords]

    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in lowered_keywords):
            selected.append(line)
        if len(selected) >= max_items:
            break

    return selected


def unique_sorted(values: Iterable[str]) -> List[str]:
    """Return unique, non-empty strings in alphabetical order."""
    return sorted(set(value.strip() for value in values if value and value.strip()))
