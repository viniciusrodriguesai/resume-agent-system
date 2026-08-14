from resume_ai.evaluation import classification_metrics


def test_metrics_are_computed():
    metrics = classification_metrics(
        ["matched", "partial", "missing"],
        ["matched", "missing", "missing"],
    )
    assert metrics["accuracy"] == 0.6667
    assert "macro_f1" in metrics
