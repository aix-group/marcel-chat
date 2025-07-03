import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from marcel.admin.auth import hash_password
from marcel.admin.routes import (
    TimeSeriesItem,
    add_month,
    add_year,
    aggregate_time_series,
    generate_aggregation_bins,
)
from marcel.models import AdminUser, Conversation, Message, User


@pytest.fixture(scope="function", autouse=True)
def seed_database(session_factory):
    with session_factory() as db_session:
        admin = AdminUser(username="johndoe", hashed_password=hash_password("secret"))
        db_session.add(admin)
        db_session.commit()


@pytest.fixture(scope="function")
def authenticated_client(test_client):
    response = test_client.post(
        "/admin/login",
        data={"username": "johndoe", "password": "secret", "grant_type": "password"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "username" in response_data
    assert response_data["username"] == "johndoe"
    assert "access_token" in response.cookies
    test_client.cookies = {"access_token": response.cookies["access_token"]}
    return test_client


def test_get_conversation(authenticated_client: TestClient, session_factory):
    with session_factory() as db_session:
        # Seed conversation
        conversation = Conversation(
            user=User(client_id=uuid.uuid4()),
            messages=[
                Message(content="Hello!", role="user"),
                Message(content="How can I help you?", role="assistant"),
            ],
            rating=4,
        )
        db_session.add(conversation)
        db_session.commit()
        conversation_id = conversation.id

    response = authenticated_client.get(f"/admin/conversation/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(conversation_id)
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hello!"
    assert data["messages"][1]["content"] == "How can I help you?"
    assert data["rating"] == 4


def test_get_conversation_unauthorized(test_client: TestClient):
    response = test_client.get(f"/admin/conversation/{uuid.uuid4()}")
    assert response.status_code == 401


def test_get_conversation_not_found(authenticated_client: TestClient):
    response = authenticated_client.get(f"/admin/conversation/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_conversations(authenticated_client: TestClient, session_factory):
    # Seed conversations
    with session_factory() as db_session:
        user = User(client_id=uuid.uuid4())
        conversations = [Conversation(user=user) for i in range(15)]
        db_session.add_all(conversations)
        db_session.commit()

    response = authenticated_client.get("/admin/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 10
    assert data["total"] == 15
    assert data["page"] == 0
    assert data["size"] == 10

    response = authenticated_client.get("/admin/conversations?size=12")
    assert len(response.json()["conversations"]) == 12

    response = authenticated_client.get("/admin/conversations?page=0&size=12")
    assert len(response.json()["conversations"]) == 12

    response = authenticated_client.get("/admin/conversations?page=0&size=5")
    assert len(response.json()["conversations"]) == 5

    response = authenticated_client.get("/admin/conversations?page=1&size=5")
    assert len(response.json()["conversations"]) == 5

    response = authenticated_client.get("/admin/conversations?page=2&size=5")
    assert len(response.json()["conversations"]) == 5

    response = authenticated_client.get("/admin/conversations?page=3&size=5")
    assert len(response.json()["conversations"]) == 0


def test_get_conversations_unauthorized(test_client: TestClient):
    response = test_client.get("/admin/conversations")
    assert response.status_code == 401


def test_get_conversations_empty(authenticated_client: TestClient):
    response = authenticated_client.get("/admin/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 0
    assert data["total"] == 0

    response = authenticated_client.get("/admin/conversations?page=-1")
    assert response.status_code == 422

    response = authenticated_client.get("/admin/conversations?page=0&size=150")
    assert response.status_code == 422


def test_get_conversations_with_message_count(
    authenticated_client: TestClient, session_factory
):
    with session_factory() as db_session:
        user_a = User(client_id=uuid.uuid4())
        user_b = User(client_id=uuid.uuid4())
        conversations = [
            Conversation(
                user=user_a,
                messages=[
                    Message(content="Hello!", role="user"),
                    Message(content="How can I help you?", role="assistant"),
                    Message(content="Foo", role="user"),
                    Message(content="Bar", role="assistant"),
                ],
                rating=4,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Conversation(
                user=user_a,
                messages=[],
                created_at=datetime.now() - timedelta(seconds=1),
                updated_at=datetime.now() - timedelta(seconds=1),
            ),
            Conversation(
                user=user_b,
                messages=[
                    Message(content="Hello!", role="user"),
                    Message(content="How can I help you?", role="assistant"),
                ],
                created_at=datetime.now() - timedelta(seconds=2),
                updated_at=datetime.now() - timedelta(seconds=2),
            ),
        ]
        db_session.add_all(conversations)
        db_session.commit()

    response = authenticated_client.get("/admin/conversations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 0
    assert data["size"] == 10
    assert len(data["conversations"]) == 3
    assert data["conversations"][0]["n_messages"] == 4
    assert data["conversations"][1]["n_messages"] == 0
    assert data["conversations"][2]["n_messages"] == 2


def test_get_statistics(authenticated_client, session_factory):
    today = date.today()
    created_at_today = datetime.combine(today, datetime.min.time())
    created_at_yesterday = created_at_today - timedelta(days=1)
    created_long_ago = created_at_today - timedelta(days=29)

    # empty database
    empty_start = today - timedelta(days=100)
    empty_end = today
    resp = authenticated_client.get(
        "/admin/statistics",
        params={
            "start_date": empty_start.isoformat(),
            "end_date": empty_end.isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["totals"]["total_conversations"] == 0
    assert data["totals"]["total_users"] == 0
    assert data["totals"]["total_messages"] == 0
    assert data["totals"]["total_average_rating"] is None

    # populate data
    with session_factory() as db:
        u1 = User(client_id=uuid.uuid4(), consent_given_at=created_at_today)
        u2 = User(client_id=uuid.uuid4(), consent_given_at=created_at_yesterday)
        u3 = User(client_id=uuid.uuid4(), consent_given_at=created_long_ago)
        db.add_all([u1, u2, u3])

        c1 = Conversation(
            user=u1,
            created_at=created_at_today,
            rating=4,
            messages=[
                Message(content="Hi", role="user", created_at=created_at_today),
                Message(
                    content="Hello!", role="assistant", created_at=created_at_today
                ),
            ],
        )
        c2 = Conversation(
            user=u2,
            created_at=created_at_yesterday,
            rating=5,
            messages=[
                Message(content="Help", role="user", created_at=created_at_yesterday),
                Message(
                    content="Sure", role="assistant", created_at=created_at_yesterday
                ),
            ],
        )
        c3 = Conversation(
            user=u3,
            created_at=created_long_ago,
            rating=3,
            messages=[
                Message(content="Old msg", role="user", created_at=created_long_ago),
                Message(
                    content="Old rsp", role="assistant", created_at=created_long_ago
                ),
                Message(
                    content="More recent", role="user", created_at=created_at_yesterday
                ),
                Message(
                    content="More recent rsp",
                    role="assistant",
                    created_at=created_at_yesterday,
                ),
            ],
        )
        db.add_all([c1, c2, c3])
        db.commit()

    # last 2 days, daily bins
    resp = authenticated_client.get(
        "/admin/statistics",
        params={
            "start_date": (today - timedelta(days=1)).isoformat(),
            "end_date": today.isoformat(),
            "agg": "day",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["totals"]["total_conversations"] == 2
    assert data["totals"]["total_users"] == 2
    assert data["totals"]["total_messages"] == 6
    assert data["totals"]["total_average_rating"] == 4.5
    assert len(data["time_series"]["conversations"]) == 2
    assert len(data["time_series"]["users"]) == 2
    assert len(data["time_series"]["messages"]) == 2
    assert len(data["time_series"]["ratings"]) == 2

    # default 30-day span, daily bins
    resp = authenticated_client.get("/admin/statistics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totals"]["total_conversations"] == 3
    assert data["totals"]["total_users"] == 3
    assert data["totals"]["total_messages"] == 8
    assert data["totals"]["total_average_rating"] == 4.0
    assert len(data["time_series"]["conversations"]) == 30

    # future span, expect only empty buckets
    future_start = today + timedelta(days=100)
    future_end = future_start + timedelta(days=1)
    resp = authenticated_client.get(
        "/admin/statistics",
        params={
            "start_date": future_start.isoformat(),
            "end_date": future_end.isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(
        item["value"] in (0, None)
        for series in data["time_series"].values()
        for item in series
    )

    # invalid span triggers 400
    resp = authenticated_client.get(
        "/admin/statistics",
        params={
            "start_date": today.isoformat(),
            "end_date": (today - timedelta(days=3)).isoformat(),
        },
    )
    assert resp.status_code == 400

    # 1-year span, weekly bins
    year_start = today - timedelta(days=365)
    resp = authenticated_client.get(
        "/admin/statistics",
        params={
            "start_date": year_start.isoformat(),
            "end_date": today.isoformat(),
            "agg": "week",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["totals"]["total_conversations"] == 3
    assert data["totals"]["total_users"] == 3
    assert data["totals"]["total_messages"] == 8
    assert data["totals"]["total_average_rating"] == 4.0
    assert len(data["time_series"]["conversations"]) == 53
    assert len(data["time_series"]["users"]) == 53
    assert len(data["time_series"]["messages"]) == 53


def test_add_month():
    assert add_month(date(2025, 1, 31)) == date(2025, 2, 28)  # January to February
    assert add_month(date(2025, 2, 28)) == date(2025, 3, 28)  # February to March
    assert add_month(date(2025, 3, 31)) == date(2025, 4, 30)  # March to April
    assert add_month(date(2025, 1, 1)) == date(2025, 2, 1)  # Start of month
    assert add_month(date(2025, 2, 15)) == date(2025, 3, 15)  # Mid-month


def test_add_year():
    assert add_year(date(2025, 1, 1)) == date(2026, 1, 1)  # Regular year
    assert add_year(date(2024, 2, 29)) == date(
        2025, 2, 28
    )  # Leap year to non-leap year
    assert add_year(date(2025, 2, 28)) == date(
        2026, 2, 28
    )  # Non-leap year to non-leap year
    assert add_year(date(2024, 5, 29)) == date(2025, 5, 29)  # Regular date


def test_generate_aggregation_bins():
    assert generate_aggregation_bins(date(2025, 1, 1), date(2025, 1, 3), "day") == [
        (date(2025, 1, 1), date(2025, 1, 2)),
        (date(2025, 1, 2), date(2025, 1, 3)),
        (date(2025, 1, 3), date(2025, 1, 3)),
    ]

    assert generate_aggregation_bins(date(2025, 1, 1), date(2025, 1, 15), "week") == [
        (date(2025, 1, 1), date(2025, 1, 8)),
        (date(2025, 1, 8), date(2025, 1, 15)),
        (date(2025, 1, 15), date(2025, 1, 15)),
    ]

    assert generate_aggregation_bins(date(2025, 1, 1), date(2025, 3, 15), "month") == [
        (date(2025, 1, 1), date(2025, 2, 1)),
        (date(2025, 2, 1), date(2025, 3, 1)),
        (date(2025, 3, 1), date(2025, 3, 15)),
    ]

    assert generate_aggregation_bins(date(2020, 2, 28), date(2022, 6, 1), "year") == [
        (date(2020, 2, 28), date(2021, 2, 28)),
        (date(2021, 2, 28), date(2022, 2, 28)),
        (date(2022, 2, 28), date(2022, 6, 1)),
    ]

    assert generate_aggregation_bins(date(2025, 5, 5), date(2025, 5, 5), "day") == [
        (date(2025, 5, 5), date(2025, 5, 5))
    ]

    assert generate_aggregation_bins(date(2025, 6, 1), date(2025, 5, 1), "day") == []

    try:
        generate_aggregation_bins(date(2025, 1, 1), date(2025, 1, 10), "invalid")
        assert False
    except KeyError:
        assert True


def test_aggregate_time_series():
    data = [
        (date(2025, 1, 1), 5),
        (date(2025, 1, 4), 7),
        (date(2025, 1, 9), 3),
        (date(2025, 1, 11), 10),
        (date(2025, 2, 12), 2),
        (date(2025, 2, 15), 4),
        (date(2025, 3, 20), 10),
    ]
    # end date is exclusive
    assert aggregate_time_series(data, date(2025, 1, 1), date(2025, 1, 15), "week") == [
        TimeSeriesItem(date=date(2025, 1, 1), value=12),
        TimeSeriesItem(date=date(2025, 1, 8), value=13),
    ]
    assert aggregate_time_series(data, date(2025, 1, 1), date(2025, 1, 15), "day") == [
        TimeSeriesItem(date=date(2025, 1, 1), value=5),
        TimeSeriesItem(date=date(2025, 1, 2), value=0),
        TimeSeriesItem(date=date(2025, 1, 3), value=0),
        TimeSeriesItem(date=date(2025, 1, 4), value=7),
        TimeSeriesItem(date=date(2025, 1, 5), value=0),
        TimeSeriesItem(date=date(2025, 1, 6), value=0),
        TimeSeriesItem(date=date(2025, 1, 7), value=0),
        TimeSeriesItem(date=date(2025, 1, 8), value=0),
        TimeSeriesItem(date=date(2025, 1, 9), value=3),
        TimeSeriesItem(date=date(2025, 1, 10), value=0),
        TimeSeriesItem(date=date(2025, 1, 11), value=10),
        TimeSeriesItem(date=date(2025, 1, 12), value=0),
        TimeSeriesItem(date=date(2025, 1, 13), value=0),
        TimeSeriesItem(date=date(2025, 1, 14), value=0),
    ]
    assert aggregate_time_series(
        data, date(2025, 1, 1), date(2025, 2, 28), "month"
    ) == [
        TimeSeriesItem(date=date(2025, 1, 1), value=25),
        TimeSeriesItem(date=date(2025, 2, 1), value=6),
    ]

    data_str = [
        ("2025-01-01", 5),
        ("2025-01-04", 7),
        ("2025-01-09", 3),
        ("2025-01-11", 10),
    ]
    assert aggregate_time_series(
        data_str, date(2025, 1, 1), date(2025, 1, 15), "week"
    ) == [
        TimeSeriesItem(date=date(2025, 1, 1), value=12),
        TimeSeriesItem(date=date(2025, 1, 8), value=13),
    ]

    # average calculation instead of sum
    data_avg = [
        (date(2025, 2, 1), None, 2.0),
        (date(2025, 2, 2), None, 4.0),
        (date(2025, 2, 8), None, 10.0),
        (date(2025, 2, 9), None, 0.0),
    ]
    assert aggregate_time_series(
        data_avg, date(2025, 2, 1), date(2025, 2, 15), "week", avg_flag=True
    ) == [
        TimeSeriesItem(date=date(2025, 2, 1), value=3.0),
        TimeSeriesItem(date=date(2025, 2, 8), value=5.0),
    ]

    same_day = [(date(2025, 3, 3), 9)]
    assert aggregate_time_series(
        same_day, date(2025, 3, 3), date(2025, 3, 4), "day"
    ) == [TimeSeriesItem(date=date(2025, 3, 3), value=9)]

    # empty queryset, expect zero or None per bin
    assert aggregate_time_series([], date(2025, 4, 1), date(2025, 4, 8), "week") == [
        TimeSeriesItem(date=date(2025, 4, 1), value=0)
    ]
    assert aggregate_time_series(
        [], date(2025, 4, 1), date(2025, 4, 8), "week", avg_flag=True
    ) == [TimeSeriesItem(date=date(2025, 4, 1), value=None)]
