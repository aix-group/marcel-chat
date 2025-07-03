import haystack
import pytest
from sqlalchemy import select

from marcel.experiments.data_loader import fingerprint
from marcel.init_data import ingest_admin_users, ingest_documents
from marcel.models import AdminUser, Document


def test_ingest_documents_database(session_factory):
    db_session = session_factory()
    # Seed database
    # Generate some fingerprints for later reuse.
    fp1 = fingerprint("1")
    fp2 = fingerprint("2")
    fp3 = fingerprint("3")
    docs = [
        Document(
            url="example1.com",
            content="Example 1",
            fingerprint=fp1,
            title="Example 1",
            favicon="icon.ico",
        ),
        Document(
            url="example2.com",
            content="Example 2",
            fingerprint=fp2,
            title="Example 2",
            favicon="icon.ico",
        ),
    ]
    db_session.add_all(docs)
    db_session.commit()

    result = db_session.query(Document).all()
    assert len(result) == 2
    assert set(doc.fingerprint for doc in result) == {fp1, fp2}

    # Ingest new documents
    new_docs = [
        {
            "url_raw": "example2.com",
            "content": "Example 2",
            "fingerprint": fp2,
            "title": "Example 2",
            "favicon": "icon.ico",
        },
        {
            "url_raw": "example3.com",
            "content": "Example 3",
            "fingerprint": fp3,
            "title": "Example 3",
            "favicon": "icon.ico",
        },
    ]
    new_docs = [haystack.Document.from_dict(doc) for doc in new_docs]

    ingest_documents(db_session, new_docs)

    result = db_session.query(Document).all()
    assert len(result) == 3
    assert set(doc.fingerprint for doc in result) == {fp1, fp2, fp3}

    # Running this again should have no effect
    ingest_documents(db_session, new_docs)

    result = db_session.query(Document).all()
    assert len(result) == 3
    assert set(doc.fingerprint for doc in result) == {fp1, fp2, fp3}


@pytest.fixture
def seed_admin_data():
    return [
        {
            "username": "johndoe",
            "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$ufD3zl+2qT0fEg6NCrqFdg$Fs7Uhdcqv0U6VnHbdUcWeYuw/zugcGrg4pY9XkgC23I",
        },
        {
            "username": "janedoe",
            "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$ufD3zl+2qT0fEg6NCrqFdg$Fs7Uhdcqv0U6VnHbdUcWeYuw/zugcGrg4pY9XkgC23I",
        },
    ]


def test_ingest_admin_users_initial(session_factory, seed_admin_data):
    db_session = session_factory()
    ingest_admin_users(db_session, seed_admin_data)

    result = db_session.execute(select(AdminUser)).scalars().all()
    assert len(result) == 2

    usernames = sorted([admin.username for admin in result])
    assert usernames == ["janedoe", "johndoe"]

    for admin in result:
        assert isinstance(admin, AdminUser)
        assert admin.hashed_password == next(
            user["hashed_password"]
            for user in seed_admin_data
            if user["username"] == admin.username
        )


def test_ingest_admin_users_update_and_insert(session_factory, seed_admin_data):
    db_session = session_factory()
    ingest_admin_users(db_session, seed_admin_data)

    # Now update one and insert a new one
    updated_admins = [
        {
            "username": "johndoe",
            "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$74FIeHLbzjz9LHyVwawfXg$yfZiXmfIkClM/kZSMUYD3pBgjcUVt+dlNEfX353nalM",
        },
        {
            "username": "foo",
            "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$1TDoLSnxBrpwYyXi6hDFbA$LZZBpiCZKP2jZKQEP2Og0MEHpmK3coApxTzORwSVdb0",
        },
    ]

    ingest_admin_users(db_session, updated_admins)

    result = db_session.execute(select(AdminUser)).scalars().all()
    assert len(result) == 3

    usernames = sorted([admin.username for admin in result])
    assert usernames == ["foo", "janedoe", "johndoe"]

    johndoe = next(admin for admin in result if admin.username == "johndoe")
    assert johndoe.hashed_password == updated_admins[0]["hashed_password"]


def test_ingest_admin_users_empty_input(session_factory):
    db_session = session_factory()
    ingest_admin_users(db_session, [])
    result = db_session.execute(select(AdminUser)).scalars().all()
    assert result == []
