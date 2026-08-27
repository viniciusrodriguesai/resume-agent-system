import pytest

from resume_ai.presentation.engine_status import backend_error_reason, runtime_status_label


@pytest.mark.parametrize(
    ("enabled", "loaded", "expected"),
    [
        (False, False, "Desativado"),
        (True, True, "Carregado"),
        (True, False, "Habilitado · fallback"),
    ],
)
def test_runtime_status_distinguishes_configuration_from_loaded_model(
    enabled: bool,
    loaded: bool,
    expected: str,
):
    assert runtime_status_label(enabled=enabled, loaded=loaded) == expected


def test_backend_error_reason_sanitizes_optional_dependency_failure():
    assert backend_error_reason("load:ModuleNotFoundError") == "dependência opcional indisponível"
    assert "ModuleNotFoundError" not in backend_error_reason("load:ModuleNotFoundError")
