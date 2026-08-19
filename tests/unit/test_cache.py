import json

from resume_ai.infrastructure.cache import SafeResultCache
from resume_ai.settings import Settings


def disk_cache_settings(tmp_path):
    return Settings(
        project_root=tmp_path,
        data_dir=tmp_path / 'data',
        cache_dir=tmp_path / 'cache',
        cache_backend='disk',
        store_anonymized_documents=True,
    )


def test_disk_cache_uses_json_and_survives_reopen(tmp_path):
    settings = disk_cache_settings(tmp_path)
    cache = SafeResultCache(settings)
    value = {'score': 82.5, 'requirements': ['Python', 'SQL']}

    cache.set('safe-key', value)

    cache_file = settings.cache_dir / 'results' / 'safe-key.json'
    assert json.loads(cache_file.read_text(encoding='utf-8'))['value'] == value
    assert SafeResultCache(settings).get('safe-key') == value


def test_disk_cache_clear_removes_json_entries(tmp_path):
    settings = disk_cache_settings(tmp_path)
    cache = SafeResultCache(settings)
    cache.set('safe-key', {'score': 82.5})

    cache.clear()

    assert cache.get('safe-key') is None
    assert not list((settings.cache_dir / 'results').glob('*.json'))
