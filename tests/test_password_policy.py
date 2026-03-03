from app.main import validate_password_strength


def test_password_policy_accepts_strong_password():
    assert validate_password_strength("SenhaForte#2026") is None


def test_password_policy_rejects_weak_password():
    assert validate_password_strength("fraca123") is not None
