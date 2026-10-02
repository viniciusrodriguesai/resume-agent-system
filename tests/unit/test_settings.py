import pytest

from resume_ai.settings import Settings


def test_profile_preserves_environment_override(monkeypatch, tmp_path):
    monkeypatch.setenv("RESUME_EMBEDDING_ENABLED", "false")
    monkeypatch.setenv("RESUME_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RESUME_CACHE_DIR", str(tmp_path / "cache"))

    settings = Settings.for_profile("demo")

    assert settings.embedding_enabled is False


def test_disk_cache_requires_explicit_anonymized_storage_consent(tmp_path):
    with pytest.raises(ValueError, match="STORE_ANONYMIZED_DOCUMENTS"):
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            cache_backend="disk",
            store_anonymized_documents=False,
        )


@pytest.mark.parametrize('profile', ['demo', 'balanced', 'complete'])
def test_profiles_use_supported_torch_embedding_backend(profile):
    settings = Settings.for_profile(profile)

    assert settings.embedding_backend == 'torch'


def test_demo_is_lexical_without_an_explicit_override(monkeypatch, tmp_path):
    monkeypatch.delenv("RESUME_EMBEDDING_ENABLED", raising=False)
    monkeypatch.setenv("RESUME_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RESUME_CACHE_DIR", str(tmp_path / "cache"))
    assert Settings(_env_file=None).embedding_enabled is False
    assert Settings.for_profile("demo").embedding_enabled is False
    assert Settings.for_profile("balanced").embedding_enabled is True
    assert Settings.for_profile("complete").embedding_enabled is True
    monkeypatch.setenv("RESUME_EMBEDDING_ENABLED", "true")
    assert Settings.for_profile("demo").embedding_enabled is True
