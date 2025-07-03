from datetime import timedelta
from time import sleep

import pytest
from fastapi import HTTPException

from marcel.admin.auth import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_token():
    token = create_token("john.doe", expires_delta=timedelta(seconds=1))
    assert isinstance(token, str)
    assert len(token) > 0
    assert token != "john.doe"
    assert decode_token(token) == "john.doe"
    sleep(1)
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == 401


def test_verify_password():
    password = "secret"
    password_hashed = hash_password(password)
    assert verify_password(password, password_hashed)
    assert not verify_password("anothersecret", password_hashed)
