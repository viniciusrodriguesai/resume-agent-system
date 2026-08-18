from resume_ai.infrastructure.history import HistoryRepository
from resume_ai.settings import Settings


def test_disabled_history_does_not_create_sqlite_database(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        history_enabled=False,
    )

    repository = HistoryRepository(settings)

    assert repository.list_recent() == []
    repository.clear()
    assert not settings.history_db.exists()
