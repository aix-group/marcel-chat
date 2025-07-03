"""
We use following naming conventions for schemas where X is the model.

| Schema Type         | Naming Convention         | Example                        |
|---------------------|---------------------------|--------------------------------|
| Input/Create        | `XCreate`                 | `ConversationCreate`           |
| Update              | `XUpdate`                 | `ConversationUpdate`           |
| Full Response       | `XRead`                   | `ConversationRead`             |
| List (paginated)    | `XList`                   | `ConversationList`             |
| List Item           | `XListItem`               | `ConversationListItem`         |
"""

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from marcel.admin.auth import get_current_admin_user
from marcel.database import get_db
from marcel.models import (
    AdminUser,
    Conversation,
    Message,
    RetrievedDocument,
    SourceRead,
    User,
)

router = APIRouter()


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    non_answer: Optional[bool]
    feedback: Optional[str]
    created_at: datetime
    sources: List[SourceRead]


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: int
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead]


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: int
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    n_messages: int = 0


class ConversationList(BaseModel):
    page: int
    size: int
    total: int
    conversations: List[ConversationListItem]


@router.get("/conversation/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin_user),
):
    conversation = db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.messages)
            .selectinload(Message.documents)
            .selectinload(RetrievedDocument.document)
        )
    ).scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=404, detail=f"Conversation with ID {conversation_id} not found."
        )

    return conversation


@router.get("/conversations")
def get_conversations(
    page: int = Query(0, ge=0),
    size: int = Query(10, le=100),
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin_user),
) -> ConversationList:
    skip = page * size
    total = db.execute(select(func.count(Conversation.id))).scalar()
    query = (
        select(Conversation, func.count(Message.id).label("n_messages"))
        .join(Message, Message.conversation_id == Conversation.id, isouter=True)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(size)
    )
    items = []
    for conversation, n_messages in db.execute(query).all():
        item = ConversationListItem.model_validate(conversation)
        item.n_messages = n_messages
        items.append(item)
    return ConversationList(page=page, size=size, total=total, conversations=items)


class TimeSeriesItem(BaseModel):
    date: date
    value: int | float | None


class StatsTimeSeries(BaseModel):
    conversations: List[TimeSeriesItem]
    users: List[TimeSeriesItem]
    messages: List[TimeSeriesItem]
    ratings: List[TimeSeriesItem]


class StatsTotal(BaseModel):
    total_conversations: int
    total_users: int
    total_messages: int
    total_average_rating: float | None


class StatisticsRead(BaseModel):
    time_series: StatsTimeSeries
    totals: StatsTotal


def add_month(d: date) -> date:
    """Add one month to the date, adjusting for month overflow."""
    year = d.year + (d.month // 12)
    month = (d.month % 12) + 1
    day = min(d.day, (date(year, (month % 12) + 1, 1) - timedelta(days=1)).day)
    return date(year, month, day)


def add_year(d: date) -> date:
    """Add one year to the date, adjusting for leap years."""
    try:
        return date(d.year + 1, d.month, d.day)
    except ValueError:
        # Handle leap year case
        return date(
            d.year + 1, d.month, 28
        )  # Fallback to February 28 if leap year fails


def generate_aggregation_bins(
    start: date, end: date, agg: str
) -> list[tuple[date, date]]:
    """Generate weekly bins from start to end date."""
    bins = []
    current = start
    # Python timedelta does not support monts and years directly,
    # so we define a mapping for aggregation periods.
    # all dates are inclusive of the start date and exclusive of the end date
    aggregation_days = {
        "day": lambda x: x + timedelta(days=1),
        "week": lambda x: x + timedelta(weeks=1),
        "month": add_month,
        "year": add_year,
    }
    time_span = aggregation_days[agg]
    while current <= end:
        bin_end = min(time_span(current), end)
        bins.append((current, bin_end))
        current = time_span(current)
    return bins


def aggregate_time_series(
    queryset: list, start: date, end: date, agg: str, avg_flag: bool = False
):
    """Aggregate a list of items into aggregation bins.
    End date is exclusive."""
    date_idx, value_idx, avg_idx = 0, 1, 2

    bins = generate_aggregation_bins(start, end, agg)
    if bins[-1][0] == bins[-1][1]:
        # If the last bin is empty, remove it
        bins.pop()
    result = []
    for bin_start, bin_end in bins:
        # Filter items that fall within the current bin

        items = [
            item
            for item in queryset
            if bin_start
            <= (
                date.fromisoformat(item[date_idx])
                if isinstance(item[date_idx], str)
                else item[date_idx]
            )
            < bin_end
        ]

        if avg_flag:
            # Calculate average for the specified key
            values = [item[avg_idx] for item in items if item[avg_idx] is not None]
            avg = sum(values) / len(values) if values else None
            result.append(TimeSeriesItem(date=bin_start, value=avg))
        else:
            # Sum the values for the current bin
            count = sum(item[value_idx] or 0 for item in items)
            result.append(TimeSeriesItem(date=bin_start, value=count))

    return result


@router.get("/statistics", response_model=StatisticsRead)
def get_statistics(
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin_user),
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=29)),
    end_date: date = Query(default_factory=date.today),
    agg: str = Query("day", pattern="^(day|week|month|year)$"),
) -> StatisticsRead:
    if start_date and end_date:
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="Invalid date range: end_date must be on or after start_date.",
            )
    end_date = end_date + timedelta(days=1)  # Include the end date in the range

    conversations_data = db.execute(
        select(
            func.date(Conversation.created_at).label("date"),
            func.count(Conversation.id).label("count"),
            func.avg(Conversation.rating).label("average_rating"),
        )
        .where(func.date(Conversation.created_at).between(start_date, end_date))
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
    ).all()

    users_data = db.execute(
        select(
            func.date(User.consent_given_at).label("date"),
            func.count(User.id).label("count"),
        )
        .where(func.date(User.consent_given_at).between(start_date, end_date))
        .group_by(func.date(User.consent_given_at))
        .order_by(func.date(User.consent_given_at))
    ).all()

    messages_data = db.execute(
        select(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("count"),
        )
        .where(func.date(Message.created_at).between(start_date, end_date))
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
    ).all()
    totals = db.execute(
        select(
            select(func.count(Conversation.id))
            .where(func.date(Conversation.created_at).between(start_date, end_date))
            .scalar_subquery()
            .label("total_conversations"),
            select(func.count(User.id))
            .where(func.date(User.consent_given_at).between(start_date, end_date))
            .scalar_subquery()
            .label("total_users"),
            select(func.count(Message.id))
            .where(func.date(Message.created_at).between(start_date, end_date))
            .scalar_subquery()
            .label("total_messages"),
            select(func.avg(Conversation.rating))
            .where(func.date(Conversation.created_at).between(start_date, end_date))
            .scalar_subquery()
            .label("total_average_rating"),
        )
    ).one()

    conversations_series = aggregate_time_series(
        conversations_data, start_date, end_date, agg
    )
    users_series = aggregate_time_series(users_data, start_date, end_date, agg)
    messages_series = aggregate_time_series(messages_data, start_date, end_date, agg)
    ratings_series = aggregate_time_series(
        conversations_data, start_date, end_date, agg, avg_flag=True
    )

    return StatisticsRead(
        time_series=StatsTimeSeries(
            conversations=conversations_series,
            users=users_series,
            messages=messages_series,
            ratings=ratings_series,
        ),
        totals=StatsTotal(
            total_conversations=totals.total_conversations,
            total_users=totals.total_users,
            total_messages=totals.total_messages,
            total_average_rating=totals.total_average_rating,
        ),
    )
