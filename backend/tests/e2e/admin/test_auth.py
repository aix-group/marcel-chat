import pytest
from fastapi.testclient import TestClient

from marcel.admin.auth import hash_password
from marcel.models import AdminUser


@pytest.fixture(scope="function", autouse=True)
def seed_database(session_factory):
    with session_factory() as db_session:
        admin = AdminUser(username="johndoe", hashed_password=hash_password("secret"))
        db_session.add(admin)
        db_session.commit()


def test_login_flow(test_client: TestClient):
    response = test_client.post(
        "/admin/login",
        data={"username": "johndoe", "password": "secret", "grant_type": "password"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert list(response_data.keys()) == ["username"]
    assert response_data["username"] == "johndoe"
    test_client.cookies = {"access_token": response.cookies["access_token"]}

    response = test_client.get("/admin/me")
    assert response.status_code == 200
    response_data = response.json()
    assert list(response_data.keys()) == ["username"]
    assert response_data["username"] == "johndoe"

    response = test_client.post("/admin/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies
    assert 'access_token="";' in response.headers["Set-Cookie"]

    test_client.cookies = {}
    response = test_client.get("/admin/me")
    assert response.status_code == 401


def test_login_wrong_password(test_client: TestClient):
    response = test_client.post(
        "/admin/login",
        data={"username": "johndoe", "password": "notright", "grant_type": "password"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


def test_login_wrong_user(test_client: TestClient):
    response = test_client.post(
        "/admin/login",
        data={"username": "notauser", "password": "secret", "grant_type": "password"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
