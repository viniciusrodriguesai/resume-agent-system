from resume_ai.agents.catalog import detect_skills


def test_manual_validation_technologies_are_structured_without_negated_terraform():
    text = """pytest
Redis
GitHub Actions
Configurei pipelines de CI/CD em produção.
Estudei conceitos de Kubernetes.
Nunca utilizei Terraform em produção.
"""

    names = {skill.name for skill in detect_skills(text)}

    assert {"pytest", "Redis", "GitHub Actions", "CI/CD", "Kubernetes"} <= names
    assert "Terraform" not in names
