from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import CHAR, ForeignKey, String, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)
from typing_extensions import Annotated


def datetime_now_utc():
    return datetime.now(timezone.utc)


str50 = Annotated[str, 50]
str100 = Annotated[str, 100]
str256 = Annotated[str, 256]
str512 = Annotated[str, 512]


class SourceRead(BaseModel):
    url: str
    score: float
    title: str
    favicon: str


class Base(MappedAsDataclass, DeclarativeBase):
    """
    Base class for all SQLAlchemy model. Using MappedAsDataclass provides type hint support when declaring new objects, and accessing object attributes.

    For a list of the default type mappings see here: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#mapped-column-derives-the-datatype-and-nullability-from-the-mapped-annotation

    We can also add custom types (e.g., a string with a maximum length of 50 characters).
    """

    type_annotation_map = {
        str50: String(50),
        str100: String(100),
        str256: String(255),
        str512: String(512),
    }


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)

    client_id: Mapped[UUID]
    consent_given: Mapped[bool] = mapped_column(default=False)
    consent_given_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user", default_factory=list
    )


class AdminUser(Base):
    __tablename__ = "admin_user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    username: Mapped[str256] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str512] = mapped_column(nullable=False)


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, index=True, init=True, default_factory=uuid4
    )
    rating: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=datetime_now_utc)
    updated_at: Mapped[datetime] = mapped_column(default_factory=datetime_now_utc)
    visible: Mapped[bool] = mapped_column(default=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), init=False)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", default_factory=list
    )
    user: Mapped["User"] = relationship(back_populates="conversations", default=None)

    @property
    def preview(self):
        if self.messages:
            first_message = sorted(self.messages, key=lambda m: m.created_at)[0]
            return first_message.content[:30]
        return ""


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    role: Mapped[str50] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    non_answer: Mapped[Optional[bool]] = mapped_column(default=None)
    cancelled_answer: Mapped[Optional[bool]] = mapped_column(default=False)
    answer_strategy: Mapped[str50] = mapped_column(default=None, nullable=True)

    generator_latency: Mapped[Optional[float]] = mapped_column(default=None)
    e2e_latency: Mapped[Optional[float]] = mapped_column(default=None)

    feedback: Mapped[Optional[str100]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=datetime_now_utc)

    # Foreign Keys
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversation.id"), init=False
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages", default=None
    )
    documents: Mapped[List["RetrievedDocument"]] = relationship(default_factory=list)

    @property
    def sources(self) -> List[SourceRead]:
        return [
            SourceRead(
                url=document.document.url,
                score=document.score,
                title=document.document.title,
                favicon=document.document.favicon,
            )
            for document in self.documents
        ]


class Document(Base):
    __tablename__ = "document"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    url: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    favicon: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(CHAR(64), index=True, unique=True)


class RetrievedDocument(Base):
    __tablename__ = "message_document_map"
    score: Mapped[float]

    message_id: Mapped[int] = mapped_column(
        ForeignKey("message.id"), primary_key=True, default=None
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id"), primary_key=True, default=None, init=False
    )

    document: Mapped["Document"] = relationship(default=None)
