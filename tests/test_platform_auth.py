from platform_core.auth import generate_api_key, hash_api_key, verify_api_key


def test_generate_api_key_is_reasonably_high_entropy() -> None:
    keys = {generate_api_key() for _ in range(100)}
    assert len(keys) == 100  # pas de collision sur 100 générations
    assert all(len(k) >= 32 for k in keys)


def test_hash_api_key_is_deterministic() -> None:
    key = generate_api_key()
    assert hash_api_key(key) == hash_api_key(key)


def test_verify_api_key_accepts_correct_key() -> None:
    key = generate_api_key()
    assert verify_api_key(key, hash_api_key(key)) is True


def test_verify_api_key_rejects_wrong_key() -> None:
    key = generate_api_key()
    other_key = generate_api_key()
    assert verify_api_key(other_key, hash_api_key(key)) is False
