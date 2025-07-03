import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from datetime import timedelta

import haystack
import numpy as np
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from marcel.app import build_app
from marcel.database import get_db, get_db_async
from marcel.models import Conversation, Document, Message, RetrievedDocument, User


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


class FakePipeline:
    """A pipeline mock with normal operation."""

    async def run_async(self, *args, **kwargs):
        documents = raw_documents()
        retrieved = [
            {**documents[0], "score": np.float64(2)},
            {**documents[2], "score": np.float64(1)},
        ]
        retrieved = [haystack.Document.from_dict(doc) for doc in retrieved]

        async def chunk_generator():
            answer_chunks = ["This ", "is ", "a ", "test ", "answer"]
            for chunk in answer_chunks:
                yield chunk

        return {
            "generated_answer": chunk_generator(),
            "documents": retrieved,
            "answer_strategy": "retrieve",
        }

    async def requires_retrieval(self, *args, **kwargs):
        return True


class FakePipelineNoRetrieval:
    async def run_async(self, *args, **kwargs):
        async def chunk_generator():
            yield "How can I help you?"

        return {
            "generated_answer": chunk_generator(),
            "documents": [],
            "answer_strategy": "generate_with_history",
        }

    async def requires_retrieval(self, *args, **kwargs):  # type: ignore
        return False


class FakePipelineWithRetrieverError:
    """A pipeline mock that fails right at the start."""

    async def run_async(self, *args, **kwargs):
        raise Exception("Something went wrong.")

    async def requires_retrieval(self, *args, **kwargs):
        return True


class FakePipelineWithGeneratorError:
    """A pipeline mock where an error occurs during generation."""

    async def run_async(self, *args, **kwargs):
        documents = raw_documents()
        retrieved = [
            {**documents[0], "score": np.float64(2)},
            {**documents[2], "score": np.float64(1)},
        ]
        retrieved = [haystack.Document.from_dict(doc) for doc in retrieved]

        async def chunk_generator():
            yield "This "
            yield "is "
            raise Exception("generator failed")

        return {
            "generated_answer": chunk_generator(),
            "documents": retrieved,
            "answer_strategy": "retrieve",
        }

    async def requires_retrieval(self, *args, **kwargs):
        return True


def create_test_client(pipeline_cls, raise_server_exceptions=False):
    @pytest_asyncio.fixture(scope="function")
    async def _fixture(session_factory_async):
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield {"pipeline": pipeline_cls()}

        def override_get_db():
            pass

        async def override_get_db_async():
            db = session_factory_async()
            try:
                yield db
            finally:
                await db.close()

        app = build_app(lifespan)
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_async] = override_get_db_async

        # AsyncClient does not call lifespan events. See:
        # https://github.com/florimondmanca/asgi-lifespan
        # https://fastapi.tiangolo.com/advanced/async-tests/
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app, raise_app_exceptions=False),
                base_url="http://test",
            ) as client:
                yield client

    return _fixture


# This creates fixtures with different pipelines
test_client = create_test_client(FakePipeline)
test_client_no_retrieval = create_test_client(FakePipelineNoRetrieval)
test_client_with_generator_error = create_test_client(FakePipelineWithGeneratorError)
test_client_with_retriever_error = create_test_client(FakePipelineWithRetrieverError)


@pytest.mark.asyncio
async def test_query(test_client, session_factory_async, mocker):
    async with session_factory_async() as db_session:
        docs = [Document(**doc) for doc in raw_documents()]
        db_session.add_all(docs)
        await db_session.commit()
        await db_session.close()

    test_user_id = uuid.uuid4()

    test_client.cookies = {"user_id": str(test_user_id)}
    streamed_chunks = []
    async with test_client.stream(
        "POST",
        "/query",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "What's the duration of the data science master (msc) program?",
                }
            ],
        },
    ) as response:
        assert response.status_code == 200

        async for chunk in response.aiter_lines():
            if chunk.strip():
                streamed_chunks.append(json.loads(chunk))

    assert len(streamed_chunks) > 1
    generated_answer = "".join(
        chunk["content"] for chunk in streamed_chunks if "content" in chunk
    )
    assert any("non_answer" in chunk for chunk in streamed_chunks[:-1]), (
        "There should be a non-answer indicator before the last chunk."
    )
    assert generated_answer == "This is a test answer"
    assert streamed_chunks[-1] == {
        "conversation_id": mocker.ANY,
        "user_message": {
            "id": mocker.ANY,
            "role": "user",
            "content": "What's the duration of the data science master (msc) program?",
            "non_answer": None,
            "feedback": None,
            "created_at": mocker.ANY,
            "sources": [],
        },
        "assistant_message": {
            "id": mocker.ANY,
            "role": "assistant",
            "content": generated_answer,
            "non_answer": False,
            "feedback": None,
            "created_at": mocker.ANY,
            "sources": [
                {
                    "url": "example1.com",
                    "score": 2,
                    "title": "Example 1",
                    "favicon": "",
                },
                {
                    "url": "example3.com",
                    "score": 1,
                    "title": "Example 3",
                    "favicon": "",
                },
            ],
        },
    }

    conversation_id = uuid.UUID(streamed_chunks[-1]["conversation_id"])
    updated_at_creation = None
    async with session_factory_async() as db_session:
        result = await db_session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(
                selectinload(Conversation.user),
                selectinload(Conversation.messages)
                .selectinload(Message.documents)
                .selectinload(RetrievedDocument.document),
            )
        )
        conversation = result.scalar_one()

        assert conversation is not None
        assert conversation.user.client_id == test_user_id
        updated_at_creation = conversation.updated_at

        messages = conversation.messages

        # One user message and one assistant message
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert (
            messages[0].content
            == "What's the duration of the data science master (msc) program?"
        )
        assert messages[0].answer_strategy == "retrieve"
        assert messages[1].role == "assistant"
        assert messages[1].content == "This is a test answer"
        assert not messages[1].answer_strategy
        assert messages[1].e2e_latency and messages[1].e2e_latency > 0
        assert messages[1].generator_latency and messages[1].generator_latency > 0
        assert messages[1].e2e_latency > messages[1].generator_latency

        assert len(messages[0].documents) == 0
        assert len(messages[1].documents) == 2

        # Assert both documents are the expected ones
        retrieved_docs = messages[1].documents
        retrieved_docs = sorted(retrieved_docs, key=lambda x: x.score, reverse=True)

        assert retrieved_docs[0].score == 2
        assert retrieved_docs[1].score == 1

        assert retrieved_docs[0].document.url == "example1.com"
        assert retrieved_docs[1].document.url == "example3.com"

        assert retrieved_docs[0].document.content == "Example 1"
        assert retrieved_docs[1].document.content == "Example 3"

    # Add another message to the conversation
    response = await test_client.post(
        "/query",
        json={
            "conversation_id": str(conversation_id),
            "messages": [
                {
                    "role": "user",
                    "content": "What's the duration of the data science master (msc) program?",
                }
            ],
        },
    )

    async with session_factory_async() as db_session:
        result = await db_session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        conversation = result.scalar_one()
        # MySQL may store timestamps without microsecond precision,
        # so we subtract a small delta to avoid false negatives in time comparison.
        assert conversation.updated_at > (updated_at_creation - timedelta(seconds=2))
        assert len(conversation.messages) == 4


@pytest.mark.asyncio
async def test_query_with_no_retrieval(
    session_factory_async, test_client_no_retrieval, mocker: MockerFixture
):
    test_client_no_retrieval.cookies = {"user_id": str(uuid.uuid4())}
    streamed_chunks = []
    async with test_client_no_retrieval.stream(
        "POST",
        "/query",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "Hello there!",
                }
            ],
        },
    ) as response:
        assert response.status_code == 200
        async for chunk in response.aiter_lines():
            if chunk.strip():
                streamed_chunks.append(json.loads(chunk))

    assert len(streamed_chunks) > 1
    generated_answer = "".join(
        chunk["content"] for chunk in streamed_chunks if "content" in chunk
    )
    assert generated_answer == "How can I help you?"
    conversation_id = uuid.UUID(streamed_chunks[-1]["conversation_id"])

    async with session_factory_async() as db_session:
        result = await db_session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(
                selectinload(Conversation.messages).selectinload(Message.documents)
            )
        )
        conversation = result.scalar_one()
        assert len(conversation.messages) == 2
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].answer_strategy == "generate_with_history"
        assert conversation.messages[1].role == "assistant"
        assert not conversation.messages[1].sources
        assert not conversation.messages[1].answer_strategy


@pytest.mark.asyncio
async def test_query_conversation_not_found(test_client):
    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = await test_client.post(
        "/query",
        json={
            "conversation_id": str(uuid.uuid4()),
            "messages": [
                {
                    "role": "user",
                    "content": "What's the duration of the data science master (msc) program?",
                }
            ],
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_conversation_forbidden(test_client, session_factory_async):
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    async with session_factory_async() as db_session:
        conversation = Conversation(
            user=User(client_id=user_a),
            messages=[Message(role="assistant", content="Test message")],
        )
        db_session.add(conversation)
        await db_session.flush()
        conversation_id = str(conversation.id)
        await db_session.commit()

    # Try to post a messages as a different user
    assert len(conversation_id) > 0
    test_client.cookies = {"user_id": str(user_b)}
    response = await test_client.post(
        "/query",
        json={
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": "user",
                    "content": "What's the duration of the data science master (msc) program?",
                }
            ],
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_query_empty_messages(test_client):
    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = await test_client.post(
        "/query",
        json={
            "messages": [],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_retriever_error(test_client_with_retriever_error):
    test_client = test_client_with_retriever_error
    test_client.cookies = {"user_id": str(uuid.uuid4())}
    response = await test_client.post(
        "/query",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "What's the duration of the data science master (msc) program?",
                }
            ],
        },
    )

    assert response.json()["detail"] == "Internal server error. Please try again."
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_query_generator_error(test_client_with_generator_error):
    test_client = test_client_with_generator_error
    test_client.cookies = {"user_id": str(uuid.uuid4())}
    streamed_chunks = []
    async with test_client.stream(
        "POST",
        "/query",
        json={
            "conversation_id": None,
            "messages": [
                {
                    "role": "user",
                    "content": "What's the duration of the data science master (msc) program?",
                }
            ],
        },
    ) as response:
        assert response.status_code == 200, (
            "Once we start streaming to the client, the http status must be 200"
        )

        async for chunk in response.aiter_lines():
            if chunk.strip():
                streamed_chunks.append(json.loads(chunk))

    assert len(streamed_chunks) > 1
    generated_answer = "".join(
        chunk["content"] for chunk in streamed_chunks if "content" in chunk
    )

    assert generated_answer == "This is ", "Answer should be partially streamed."
    error_chunk = streamed_chunks[-1]
    assert "error_status_code" in error_chunk, "Last chunk should contain error"
    assert "error_content" in error_chunk, "Last chunk should contain error"

    assert error_chunk["error_status_code"] == 500
    assert (
        error_chunk["error_content"]["detail"]
        == "Could not generate response. Please retry."
    )
