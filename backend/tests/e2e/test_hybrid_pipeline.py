import pytest
from haystack import Document
from pytest_mock import MockerFixture

from marcel.experiments.hybrid_pipeline import (
    FAQ_EMBEDDING_MODEL,
    HybridPipeline,
    get_pipeline,
)


@pytest.fixture(scope="module", autouse=True)
def download_models():
    # As the backend should run on a read-only fs, we need to ensure that embedding model is pre-loaded in test environment. This only applies to the hybrid pipeline at the moment
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder

    SentenceTransformersDocumentEmbedder(model=FAQ_EMBEDDING_MODEL).warm_up()


@pytest.mark.asyncio
async def test_run_faq_retrieval(mocker: MockerFixture):
    docs = [
        Document(content="Today: Banana", meta={"url": "example.com"}),
        Document(
            content="Each day we have a different 'fruit of the day'.",
            meta={"url": "foo.com"},
        ),
    ]

    faqs = [
        Document(
            content="What is the fruit of the day?",
            meta={"sources": ["example.com"]},
        ),
        Document(
            content="Where to find more information?",
            meta={"sources": ["foo.com"]},
        ),
    ]

    pipeline = HybridPipeline(docs, faqs)
    pipeline.requires_retrieval = mocker.AsyncMock(return_value=True)

    query = "What is todays fruit?"
    result = await pipeline.run_async(query, history=[], debug=True)
    assert result["answer_strategy"] == "retrieve"
    assert len(result["raw"]["faq_retriever"]["documents"]) == 1
    assert len(result["raw"]["bm25_retriever"]["documents"]) == 2
    assert len(result["raw"]["content_link_normalizer"]["documents"]) == 2

    generated_answer = ""
    async for chunk in result["generated_answer"]:
        generated_answer += chunk
    assert "banana" in generated_answer.lower()  # Check spyword


@pytest.mark.asyncio
async def test_run_async(mocker: MockerFixture):
    documents = [
        Document(
            content="My name is Jean and I live in Paris.", meta={"url": "foo.com"}
        ),
        Document(
            content="My name is Mark and I live in Berlin.", meta={"url": "bar.com"}
        ),
        Document(
            content="My name is Giorgio and I live in Rome.",
            meta={"url": "example.com"},
        ),
    ]
    pipeline = HybridPipeline(documents, faqs=[])
    pipeline.requires_retrieval = mocker.AsyncMock(return_value=True)

    question_answers = [
        ("Who lives in Paris?", "Jean"),
        ("Who lives in Berlin?", "Mark"),
        ("Who lives in Rome?", "Giorgio"),
    ]
    for question, expected_answer in question_answers:
        result = await pipeline.run_async(question, history=[])

        assert len(result["documents"]) > 0
        generated_answer = ""
        async for chunk in result["generated_answer"]:
            generated_answer += chunk

        assert expected_answer in generated_answer
        assert result["answer_strategy"] == "retrieve"


def test_faq_without_parent(caplog):
    docs = [
        Document(content="Example", meta={"url": "example.com"}),
    ]

    faqs = [
        Document(
            content="What is RAG?",
            meta={"sources": ["foo.com"]},
        )
    ]

    get_pipeline(docs, faqs)
    assert "No parent for faq" in caplog.text


@pytest.mark.asyncio
async def test_requires_retrieval():
    p = HybridPipeline(documents=[], faqs=[])

    def f(x):
        return p.requires_retrieval(x, max_retries=5, timeout=10)

    assert await f("What is spaghetti Carbonara?")
    assert await f("Who is the chancellor of Germany?")
    assert await f("Do I need to submit anything apart from transcripts?")
    assert not await f("Thank you!")
    assert not await f("What's up?")
    assert not await f("Nice to meet you.")


@pytest.mark.asyncio
async def test_run_async_generate_with_history_strategy(mocker: MockerFixture):
    p = HybridPipeline(documents=[], faqs=[])
    p.requires_retrieval = mocker.AsyncMock(return_value=False)
    p.retrieve = mocker.MagicMock()

    result = await p.run_async("Thank you!", history=[])
    p.retrieve.assert_not_called()
    generated_answer = ""
    async for chunk in result["generated_answer"]:
        generated_answer += chunk
    assert len(generated_answer) > 0
    assert result["answer_strategy"] == "generate_with_history"
    assert not result["documents"]
