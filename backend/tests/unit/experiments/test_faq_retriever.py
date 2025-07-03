from haystack import Document

from marcel.experiments.faq_retriever import (
    DocumentDeduplicator,
    FAQRetriever,
    ParentDocumentRetriever,
)


def test_faq_retriever():
    jean = Document(
        content="My name is Jean and I live in Paris.",
        meta={"url": "jean.fr"},
    )
    mark = Document(
        content="My name is Mark and I live in Berlin.",
        meta={"url": "mark.de"},
    )
    giorgio = Document(
        content="My name is Giorgio and I live in Rome.",
        meta={"url": "giorgio.it"},
    )
    documents = [jean, mark, giorgio]

    faqs = [
        Document(
            content="Who lives in Paris?",
            meta={"sources": ["jean.fr"]},
        ),
        Document(
            content="Who is italian?",
            meta={"sources": ["giorgio.it"]},
        ),
    ]

    faq_retriever = FAQRetriever(documents, faqs, top_k=2)
    result = faq_retriever.run(text="Who is from Italy?")  # type: ignore
    assert len(result["documents"]) == 2
    assert result["documents"][0].id == giorgio.id
    assert result["documents"][1].id == jean.id

    faq_retriever = FAQRetriever(documents, faqs, top_k=1)
    result = faq_retriever.run(text="Who is from Paris?")  # type: ignore
    assert len(result["documents"]) == 1
    assert result["documents"][0].id == jean.id

    faq_retriever = FAQRetriever(documents, [], top_k=1)
    result = faq_retriever.run(text="Who is from Paris?")  # type: ignore
    assert len(result["documents"]) == 0


def test_document_deduplicator():
    deduplicator = DocumentDeduplicator()

    # different IDs, keep all
    docs = [
        Document(id="1", content="Paris is the capital of France.", score=3),
        Document(id="2", content="Rome is the capital of Italy.", score=2),
        Document(id="3", content="Rome is the capital of Italy.", score=1),
    ]
    assert deduplicator.run(docs)["documents"] == docs

    # same Id, keep only first
    docs = [
        Document(id="1", content="Paris is the capital of France.", score=3),
        Document(id="2", content="Rome is the capital of Italy.", score=2),
        Document(id="2", content="Rome is the capital of Italy.", score=1),
    ]
    assert deduplicator.run(docs)["documents"] == [
        Document(id="1", content="Paris is the capital of France.", score=3),
        Document(id="2", content="Rome is the capital of Italy.", score=2),
    ]


def test_parent_document_retriever():
    # One parent by document
    docs = [
        Document(id="1", content="Paris is the capital of France."),
        Document(id="2", content="Rome is the capital of Italy."),
    ]
    parent_document_retriever = ParentDocumentRetriever(documents=docs)

    children = [
        Document(
            content="What is the captial of France?", meta={"parent_id": "1"}, score=3
        ),
        Document(
            content="What is the capital of Italy?", meta={"parent_id": "2"}, score=2
        ),
    ]
    assert parent_document_retriever.run(children)["documents"] == [
        Document(id="1", content="Paris is the capital of France.", score=3),
        Document(id="2", content="Rome is the capital of Italy.", score=2),
    ]

    # Multiple parents by document
    children = [
        Document(
            content="What do Paris and Rome have in common?",
            meta={"parent_id": ["1", "2"]},
            score=3,
        ),
    ]
    retrieved = parent_document_retriever.run(children)["documents"]
    assert retrieved == [
        Document(id="1", content="Paris is the capital of France.", score=3),
        Document(id="2", content="Rome is the capital of Italy.", score=3),
    ]

    # Non-existent parent
    children = [
        Document(
            content="What is the capital of Germany?", meta={"parent_id": "xx"}, score=1
        ),
    ]
    assert parent_document_retriever.run(children)["documents"] == []
