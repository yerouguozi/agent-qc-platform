from app.gateway.auth import generate_api_key, hash_key, verify_key


def test_generate_unique():
    assert generate_api_key().startswith("qc_")
    assert generate_api_key() != generate_api_key()


def test_hash_verify_roundtrip():
    key = generate_api_key()
    stored = hash_key(key)
    assert stored != key
    assert verify_key(key, stored)
    assert not verify_key("wrong", stored)


def test_verify_malformed():
    assert not verify_key("k", "not-a-hash")