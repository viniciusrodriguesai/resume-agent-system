from resume_ai.infrastructure.privacy import PrivacyService
from resume_ai.settings import Settings


def test_regex_privacy_removes_ptbr_pii(tmp_path):
    settings = Settings(project_root=tmp_path, data_dir=tmp_path / "data", cache_dir=tmp_path / "cache", presidio_enabled=False)
    text, report = PrivacyService(settings).anonymize("""Vinicius Mangueira
vinicius@example.com
CPF 123.456.789-00
(83) 99999-9999""")
    assert "vinicius@example.com" not in text
    assert "123.456.789-00" not in text
    assert report.total_removed >= 3


def test_regex_privacy_removes_address_birth_date_and_social_handle(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        presidio_enabled=False,
    )
    original = """Maria da Silva
Data de nascimento: 10/02/1998
Rua das Flores, 123 - Sao Paulo
LinkedIn: maria-silva
Python e SQL
"""

    text, report = PrivacyService(settings).anonymize(original)

    assert "10/02/1998" not in text
    assert "Rua das Flores" not in text
    assert "maria-silva" not in text
    assert report.total_removed >= 4
