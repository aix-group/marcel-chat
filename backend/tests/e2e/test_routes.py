import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from marcel.models import Conversation, Document, Message, RetrievedDocument, User
from marcel.routes import get_current_user

TEST_USER_ID = uuid.uuid4()


def raw_documents():
    documents = [
        {
            "url": "example1.com",
            "content": "Example 1",
            "title": "Example 1",
            "favicon": "",
        },
        {
            "url": "example2.com",
            "content": "Example 2",
            "title": "Example 2",
            "favicon": "",
        },
        {
            "url": "example3.com",
            "content": "Example 3",
            "title": "Example 3",
            "favicon": "",
        },
    ]

    for doc in documents:
        doc["fingerprint"] = hashlib.sha256(str(doc).encode("utf-8")).hexdigest()

    return documents


@pytest.fixture(scope="function")
def seed_database(session_factory):
    docs = [Document(**doc) for doc in raw_documents()]
    with session_factory() as db_session:
        db_session.add_all(docs)
        db_session.commit()


def test_feedback_route(test_client, session_factory):
    test_client.cookies = {"user_id": str(TEST_USER_ID)}

    # Create a test message in the database
    with session_factory() as db_session:
        conversation = Conversation(
            user=User(client_id=TEST_USER_ID),
            messages=[Message(role="assistant", content="Test message")],
        )
        db_session.add(conversation)
        db_session.commit()
        message = conversation.messages[0]

    # Post new feedback
    response = test_client.post(
        "/feedback", json={"message_id": message.id, "feedback": "good"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    with session_factory() as db_session:
        updated_message = db_session.query(Message).filter_by(id=message.id).one()
    assert updated_message.feedback == "good"

    # Clear feedback
    response = test_client.post(
        "/feedback", json={"message_id": message.id, "feedback": None}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    with session_factory() as db_session:
        updated_message = db_session.query(Message).filter_by(id=message.id).one()
    assert updated_message.feedback is None

    response = test_client.post(
        "/feedback", json={"message_id": -1, "feedback": "good"}
    )
    assert response.status_code == 404


def test_feedback_forbidden(test_client, session_factory):
    user_owner = uuid.uuid4()
    user_other = uuid.uuid4()

    with session_factory() as db_session:
        conversation = Conversation(
            user=User(client_id=user_owner),
            messages=[Message(role="assistant", content="Test message")],
        )
        db_session.add(conversation)
        db_session.commit()
        message = conversation.messages[0]

    # Posting feedback as another user should not be allowed
    test_client.cookies = {"user_id": str(user_other)}
    response = test_client.post(
        "/feedback", json={"message_id": message.id, "feedback": "good"}
    )
    assert response.status_code == 403


def test_rating(test_client, session_factory):
    with session_factory() as db_session:
        conversation = Conversation(
            user=User(client_id=TEST_USER_ID),
        )
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    # No rating exists
    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.status_code == 200
    assert not response.json()["rating"]

    # Post rating
    response = test_client.post(
        "/rating", json={"conversation_id": str(conversation_id), "rating": 10}
    )
    assert response.status_code == 200

    with session_factory() as db_session:
        conversation = (
            db_session.query(Conversation)
            .where(Conversation.id == conversation.id)
            .one()
        )
    assert conversation.rating == 10


def test_rating_conversation_not_found(test_client):
    # Rating for non-existent conversation
    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.post(
        "/rating", json={"conversation_id": str(uuid.uuid4()), "rating": 10}
    )
    assert response.status_code == 404


def test_rating_forbidden(test_client, session_factory):
    with session_factory() as db_session:
        conversation = Conversation(
            user=User(client_id=uuid.uuid4()),
        )
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    # Test with another user
    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = test_client.post(
        "/rating", json={"conversation_id": str(conversation_id), "rating": 10}
    )
    assert response.status_code == 403


def test_get_conversations(test_client, session_factory, mocker, seed_database):
    with session_factory() as db_session:
        documents = db_session.query(Document).all()
        user = User(client_id=TEST_USER_ID)
        c1 = Conversation(
            user=user,
            rating=10,
            messages=[
                Message(
                    content="how are you?",
                    role="user",
                ),
                Message(
                    content="good, thanks!",
                    role="assistant",
                    documents=[
                        RetrievedDocument(score=3, document=documents[0]),
                        RetrievedDocument(score=2, document=documents[1]),
                    ],
                ),
            ],
        )
        c2 = Conversation(
            user=user,
            messages=[
                Message(
                    content="What are the admission requirements?",
                    role="user",
                ),
                Message(
                    content="You need a bachelor degree in computer science.",
                    role="assistant",
                    documents=[
                        RetrievedDocument(score=3, document=documents[0]),
                    ],
                ),
            ],
        )
        db_session.add_all([c1, c2])
        db_session.commit()
        c1_messages = c1.messages
        c2_messages = c2.messages

    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.get("/conversations/")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    response_data = {conversation["id"]: conversation for conversation in response_data}
    assert response_data[str(c1.id)] == {
        "id": str(c1.id),
        "created_at": c1.created_at.isoformat(),
        "updated_at": c1.updated_at.isoformat(),
        "rating": 10,
        "preview": c1_messages[0].content[:30],
    }

    assert response_data[str(c2.id)] == {
        "id": str(c2.id),
        "created_at": c2.created_at.isoformat(),
        "updated_at": c2.updated_at.isoformat(),
        "rating": None,
        "preview": c2_messages[0].content[:30],
    }

    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = test_client.get("/conversations/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_conversation(test_client, session_factory, mocker, seed_database):
    with session_factory() as db_session:
        documents = db_session.query(Document).all()
        conversation = Conversation(
            user=User(client_id=TEST_USER_ID),
            rating=10,
            messages=[
                Message(
                    content="how are you?",
                    role="user",
                ),
                Message(
                    content="good, thanks!",
                    role="assistant",
                    documents=[
                        RetrievedDocument(score=3, document=documents[0]),
                        RetrievedDocument(score=2, document=documents[1]),
                    ],
                ),
            ],
        )
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.status_code == 200
    assert response.json() == {
        "id": mocker.ANY,
        "rating": 10,
        "created_at": mocker.ANY,
        "updated_at": mocker.ANY,
        "messages": [
            {
                "id": mocker.ANY,
                "role": "user",
                "content": "how are you?",
                "non_answer": None,
                "feedback": None,
                "created_at": mocker.ANY,
                "sources": [],
            },
            {
                "id": mocker.ANY,
                "role": "assistant",
                "content": "good, thanks!",
                "non_answer": None,
                "feedback": None,
                "created_at": mocker.ANY,
                "sources": [
                    {
                        "url": "example1.com",
                        "score": 3.0,
                        "title": "Example 1",
                        "favicon": "",
                    },
                    {
                        "url": "example2.com",
                        "score": 2.0,
                        "title": "Example 2",
                        "favicon": "",
                    },
                ],
            },
        ],
    }


def test_get_conversation_forbidden(test_client, session_factory, seed_database):
    with session_factory() as db_session:
        conversation = Conversation(
            user=User(client_id=TEST_USER_ID),
            rating=10,
            messages=[],
        )
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.status_code == 200

    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.status_code == 403


def test_get_conversation_not_found(test_client: TestClient):
    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.get(f"/conversation/{uuid.uuid4()}")
    assert response.status_code == 404


def test_hide_conversation(test_client: TestClient, session_factory):
    with session_factory() as db_session:
        conversation = Conversation(user=User(client_id=TEST_USER_ID), messages=[])
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.json()["id"] == str(conversation_id)

    response = test_client.get("/conversations")
    assert len(response.json()) == 1

    # after hiding the conversation it should not be visible anymore
    response = test_client.put(f"/conversation/{conversation_id}/hide")
    assert response.status_code == 204

    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.status_code == 404

    response = test_client.get("/conversations")
    assert len(response.json()) == 0

    # hiding a conversation again should be a no-op
    response = test_client.put(f"/conversation/{conversation_id}/hide")
    assert response.status_code == 204

    response = test_client.get(f"/conversation/{conversation_id}")
    assert response.status_code == 404


def test_hide_converstaion_not_found(test_client: TestClient):
    test_client.cookies = {"user_id": str(TEST_USER_ID)}
    response = test_client.put(f"/conversation/{uuid.uuid4()}/hide")
    assert response.status_code == 404


def test_hide_conversation_forbidden(test_client: TestClient, session_factory):
    with session_factory() as db_session:
        conversation = Conversation(user=User(client_id=TEST_USER_ID), messages=[])
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = test_client.put(f"/conversation/{conversation_id}/hide")
    assert response.status_code == 403


def test_start_session(test_client):
    test_client.cookies = None
    response = test_client.get("/start_session")
    assert response.status_code == 200
    assert "user_id" in response.json()
    user_id = response.cookies["user_id"]
    assert len(user_id) > 0

    # Calling the endpoint again should return the same user ID and does not generate a new cookie
    test_client.cookies = {"user_id": user_id}
    response = test_client.get("/start_session")
    assert response.status_code == 200
    assert response.json() == {"user_id": user_id}
    assert "user_id" not in response.cookies


def test_put_user_consent(test_client, session_factory):
    test_client.cookies = None
    response = test_client.get("/start_session")
    assert response.status_code == 200
    user_id = response.cookies["user_id"]
    assert len(user_id) > 0

    with session_factory() as db_session:
        user = (
            db_session.query(User)
            .where(User.client_id == uuid.UUID(user_id))
            .one_or_none()
        )
        assert user is None

    # Calling consent should create a new user with consent
    # MySQL may store timestamps without microsecond precision,
    # so we subtract a small delta to avoid false negatives in time comparison.
    time_before_request = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        seconds=2
    )
    test_client.cookies = {"user_id": user_id}
    response = test_client.put("/me/consent")
    assert response.status_code == 200
    with session_factory() as db_session:
        user = db_session.query(User).where(User.client_id == uuid.UUID(user_id)).one()
        assert user.consent_given
        assert user.consent_given_at > time_before_request


def test_get_current_user(session_factory):
    user_id = uuid.uuid4()

    with session_factory() as db_session:
        user = db_session.query(User).where(User.client_id == user_id).one_or_none()
        assert user is None

    with session_factory() as db_session:
        user = get_current_user(user_id, db_session)
        assert user.client_id == user_id

    with session_factory() as db_session:
        user = db_session.query(User).where(User.client_id == user_id).one_or_none()
        assert user is not None
