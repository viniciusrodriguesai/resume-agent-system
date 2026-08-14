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
