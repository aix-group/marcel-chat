import json
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from haystack.dataclasses import Document as HaystackDocument
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from marcel import __git_commit__, __version__
from marcel.database import get_db, get_db_async
from marcel.models import (
    Conversation,
    Document,
    Message,
    RetrievedDocument,
    SourceRead,
    User,
)
from marcel.utils.route_preprocessing import detect_non_answer, format_known_links

logger = logging.getLogger(__name__)
router = APIRouter()


class StartSessionResponse(BaseModel):
    user_id: uuid.UUID


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str


class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    messages: List[ChatMessage]


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: ChatRole
    content: str
    non_answer: Optional[bool]
    feedback: Optional[str]
    created_at: datetime
    sources: List[SourceRead]


class ChatResponseChunk(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    user_message: Optional[MessageRead] = None
    assistant_message: Optional[MessageRead] = None
    content: Optional[str] = None
    non_answer: Optional[bool] = None

    # Once streaming started, the request is marked successfull (i.e., http-status 200).
    # We return the attributes below to alert clients of errors *while* streaming.
    error_status_code: Optional[int] = None
    error_content: Optional[Dict[str, Any]] = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead]


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    preview: str


class MessageFeedbackRequest(BaseModel):
    message_id: int
    feedback: Literal["good", "bad", None]


class ConversationRatingRequest(BaseModel):
    conversation_id: uuid.UUID
    rating: int


@router.get("/status")
def status():
    return {"status": "ok"}


class VersionResponse(BaseModel):
    version: str
    commit: str


@router.get("/version")
def version() -> VersionResponse:
    return VersionResponse(version=__version__, commit=__git_commit__)


@router.get("/start_session")
def start_session(
    response: Response,
    user_id: Annotated[uuid.UUID | None, Cookie()] = None,
) -> StartSessionResponse:
    if not user_id:
        user_id = uuid.uuid4()
        response.set_cookie(
            key="user_id",
            value=str(user_id),
            max_age=60 * 60 * 24 * 30,  # 30 days in seconds
            httponly=True,  # Prevent JavaScript from acessing the cookie
            samesite="strict",  # Only send cookies with requests from same origin
            secure=True,  # Only send cookie on https requests
        )

    return StartSessionResponse(user_id=user_id)


def get_current_user(
    user_id: Annotated[uuid.UUID, Cookie()], db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.client_id == user_id).one_or_none()
    if not user:
        user = User(client_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def get_current_user_async(
    user_id: Annotated[uuid.UUID, Cookie()], db: AsyncSession = Depends(get_db_async)
) -> User:
    result = await db.execute(select(User).filter(User.client_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(client_id=user_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


@router.put("/me/consent")
def put_consent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.consent_given = True
    user.consent_given_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    return {"status": "success"}


@router.post("/query", response_model=ChatResponseChunk)
async def query(
    chat_request: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db_async),
):
    if not chat_request.messages:
        raise HTTPException(status_code=422, detail="No messages provided.")

    if chat_request.conversation_id:
        # verify conversation existence and ownership before proceeding
        await get_conversation_db_async(db, chat_request.conversation_id, user)

    e2e_start = time.time()
    query = chat_request.messages[-1].content
    history = [message for message in chat_request.messages[:-1]]
    response = await request.state.pipeline.run_async(query, history)

    def encode_chunk(chunk: ChatResponseChunk):
        # Each streaming chunk contains different payload.
        # exclude_unset=True keeps the returned json clean
        return json.dumps(jsonable_encoder(chunk, exclude_unset=True)) + "\n"

    async def response_generator():
        try:
            generated_answer = ""
            generator_start = time.time()
            async for chunk in response["generated_answer"]:
                generated_answer += chunk
                yield encode_chunk(ChatResponseChunk(content=chunk))
            generator_end = time.time()

            links = {}
            for doc in response["documents"]:
                links.update(doc.meta.get("links", {}))
            formatted_answer, formatted_links = format_known_links(
                generated_answer, links
            )
            non_answer_verdict = detect_non_answer(formatted_answer)
            if formatted_links.strip():
                yield encode_chunk(ChatResponseChunk(content=f"\n\n{formatted_links}"))
            yield encode_chunk(ChatResponseChunk(non_answer=non_answer_verdict))

            if chat_request.conversation_id:
                conversation = await get_conversation_db_async(
                    db, chat_request.conversation_id, user
                )
            else:
                conversation = Conversation(user=user)

            e2e_end = time.time()
            user_log = Message(
                role="user",
                content=query,
                answer_strategy=response["answer_strategy"],
            )
            assistant_log = Message(
                role="assistant",
                content=formatted_answer,
                documents=await build_retrieved_docs(db, response["documents"]),
                non_answer=non_answer_verdict,
                e2e_latency=e2e_end - e2e_start,
                generator_latency=generator_end - generator_start,
            )
            conversation.messages.append(user_log)
            conversation.messages.append(assistant_log)
            conversation.updated_at = datetime.now(timezone.utc)
            db.add(conversation)
            await db.flush()  # ensure IDs are populated

            yield encode_chunk(
                ChatResponseChunk(
                    conversation_id=conversation.id,
                    user_message=MessageRead.model_validate(user_log),
                    assistant_message=MessageRead.model_validate(assistant_log),
                )
            )
            await db.commit()
        except Exception as e:
            logger.exception("Streaming failed. Request: %s", repr(chat_request))

            if isinstance(e, HTTPException):
                status_code = e.status_code
                content = {"detail": e.detail}
            else:
                status_code = http_status.HTTP_500_INTERNAL_SERVER_ERROR
                content = {"detail": "Could not generate response. Please retry."}

            yield encode_chunk(
                ChatResponseChunk(
                    error_status_code=status_code,
                    error_content=content,
                )
            )
        finally:
            # Ensure session is properly closed once the generator ends. The call to db.rollback() does nothing if the transaction was already committed. It added as we can't be certain whether or not the current session was dirty (e.g., when catching an exception).
            await db.rollback()
            await db.close()

    return StreamingResponse(response_generator())


async def build_retrieved_docs(db: AsyncSession, documents: List[HaystackDocument]):
    fingerprints = [doc.meta["fingerprint"] for doc in documents]
    result = await db.execute(
        select(Document).where(Document.fingerprint.in_(fingerprints))
    )
    fingerprint_to_doc = {doc.fingerprint: doc for doc in result.scalars().all()}
    retrieved_docs = [
        RetrievedDocument(
            document=fingerprint_to_doc[doc.meta["fingerprint"]],
            score=float(doc.score) if doc.score else 0,
        )
        for doc in documents
    ]
    return retrieved_docs


async def get_conversation_db_async(
    db: AsyncSession, conversation_id: uuid.UUID, user: User
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if conversation.user_id != user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation.",
        )

    return conversation


@router.post("/feedback")
def submit_feedback(
    feedback_request: MessageFeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(
            Message.id == feedback_request.message_id,
            Message.role == "assistant",
        )
        .one_or_none()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.conversation.user_id != user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation.",
        )

    message.feedback = feedback_request.feedback
    db.commit()
    db.refresh(message)
    return {"status": "success"}


@router.post("/rating")
def submit_rating_feedback(
    feedback_request: ConversationRatingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.execute(
        select(Conversation).where(Conversation.id == feedback_request.conversation_id)
    ).scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if conversation.user_id != user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation.",
        )

    conversation.rating = feedback_request.rating
    db.commit()
    db.refresh(conversation)
    return {"status": "success"}


@router.get("/conversation/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.visible)
        .options(
            selectinload(Conversation.messages)
            .selectinload(Message.documents)
            .selectinload(RetrievedDocument.document)
        )
    ).scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if conversation.user_id != user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation.",
        )

    return conversation


@router.put(
    "/conversation/{conversation_id}/hide", status_code=http_status.HTTP_204_NO_CONTENT
)
def hide_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    ).scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if conversation.user_id != user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation.",
        )

    if conversation.visible:
        conversation.visible = False
        db.commit()


@router.get("/conversations", response_model=List[ConversationListItem])
def get_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id, Conversation.visible)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
        )
        .scalars()
        .all()
    )

    return result
