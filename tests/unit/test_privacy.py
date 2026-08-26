import pytest

from resume_ai.infrastructure.privacy import PrivacyService
from resume_ai.settings import Settings


def test_regex_privacy_removes_ptbr_pii(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        presidio_enabled=False,
    )
    text, report = PrivacyService(settings).anonymize("""Alex Example
alex@example.invalid
CPF 123.456.789-00
(00) 90000-0000""")
    assert "alex@example.invalid" not in text
    assert "123.456.789-00" not in text
    assert report.total_removed >= 3


def test_regex_privacy_removes_address_birth_date_and_social_handle(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        presidio_enabled=False,
    )
    original = """Maria Example
Data de nascimento: 10/02/1998
Rua Exemplo, 123 - Cidade Ficticia
LinkedIn: maria-example
Python e SQL
"""

    text, report = PrivacyService(settings).anonymize(original)

    assert "10/02/1998" not in text
    assert "Rua Exemplo" not in text
    assert "maria-example" not in text
    assert report.total_removed >= 4


@pytest.mark.parametrize(
    "original",
    [
        "CURRÍCULO\nMaria Silva\nPython e SQL",
        "RESUME\nAlex Example\nPython e SQL",
        "Nome: Maria Silva\nPython e SQL",
        "Full name: Alex Example\nPython e SQL",
    ],
)
def test_regex_privacy_removes_name_after_resume_heading_or_label(
    tmp_path,
    original: str,
) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        presidio_enabled=False,
    )

    text, report = PrivacyService(settings).anonymize(original)

    assert "Maria Silva" not in text
    assert "Alex Example" not in text
    assert "Python e SQL" in text
    assert any(entity.entity_type == "NOME_CANDIDATO" for entity in report.entities)


def test_regex_privacy_does_not_remove_technical_lines_after_heading(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        presidio_enabled=False,
    )
    original = "CURRÍCULO\nPython\nFastAPI\nPostgreSQL"

    text, report = PrivacyService(settings).anonymize(original)

    assert "Python" in text
    assert "FastAPI" in text
    assert "PostgreSQL" in text
    assert all(entity.entity_type != "NOME_CANDIDATO" for entity in report.entities)


@pytest.mark.parametrize(
    ("original", "private_name", "technical_line"),
    [
        ("Nome completo: Maria Silva\nPython", "Maria Silva", "Python"),
        ("CURRÍCULO\nJosé da Silva\nPython", "José da Silva", "Python"),
        ("CV\nJoão D'Ávila\nFastAPI", "João D'Ávila", "FastAPI"),
        ("RESUME\n김민수\nPython 개발 경험", "김민수", "Python 개발 경험"),
        ("CV\n李伟\nPython 开发经验", "李伟", "Python 开发经验"),
    ],
)
def test_regex_privacy_handles_labeled_and_unicode_names_without_losing_technical_text(
    tmp_path,
    original: str,
    private_name: str,
    technical_line: str,
) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        presidio_enabled=False,
    )

    text, report = PrivacyService(settings).anonymize(original)

    assert private_name not in text
    assert technical_line in text
    assert any(entity.entity_type == "NOME_CANDIDATO" for entity in report.entities)
