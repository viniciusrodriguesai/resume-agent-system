import json
from concurrent.futures import ThreadPoolExecutor

from resume_ai.infrastructure.cache import SafeResultCache
from resume_ai.settings import Settings


def disk_cache_settings(tmp_path, **overrides):
    return Settings(
        project_root=tmp_path,
        data_dir=tmp_path / 'data',
        cache_dir=tmp_path / 'cache',
        cache_backend='disk',
        store_anonymized_documents=True,
        **overrides,
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


def test_disk_cache_serializes_concurrent_writes_to_the_same_key(tmp_path):
    cache = SafeResultCache(disk_cache_settings(tmp_path))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda value: cache.set('shared-key', {'sentinel': f'DOC-{value}'}),
                range(40),
            )
        )

    stored = cache.get('shared-key')
    assert stored is not None
    assert stored['sentinel'].startswith('DOC-')
    assert not list(cache.path.glob('*.tmp'))


def test_disk_cache_evicts_oldest_entries_at_configured_limit(tmp_path):
    cache = SafeResultCache(disk_cache_settings(tmp_path, cache_max_entries=2))

    cache.set('first', {'sentinel': 'DOC-A'})
    cache.set('second', {'sentinel': 'DOC-B'})
    cache.set('third', {'sentinel': 'DOC-C'})

    assert cache.get('first') is None
    assert cache.get('second') == {'sentinel': 'DOC-B'}
    assert cache.get('third') == {'sentinel': 'DOC-C'}
    assert len(list(cache.path.glob('*.json'))) == 2
