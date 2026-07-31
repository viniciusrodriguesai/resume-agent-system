from resume_ai.privacy import anonymize_resume

def test_privacy_removes_direct_identifiers():
    text = """
    Alex Example
    alex@example.com
    +55 83 99999-0000
    Date of birth: 2000-01-01
    Python developer
    """
    anonymized, report = anonymize_resume(text)
    assert "alex@example.com" not in anonymized
    assert "99999-0000" not in anonymized
    assert "Date of birth" not in anonymized
    assert report["email_removed"] == 1
