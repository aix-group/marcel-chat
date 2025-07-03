import pytest
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

from marcel.experiments.oracle_retriever import BM25RetrieverWithOracle

documents = [
    Document(id="a", content="apple"),
    Document(id="b", content="banana"),
    Document(id="c", content="cranberry"),
    Document(id="d", content="date"),
]

store = InMemoryDocumentStore()
store.write_documents(documents)


def get_filter(id_):
    return {"field": "id", "operator": "==", "value": id_}


def test_default_mode():
    # Should only return documents that match query and filter
    retriever = BM25RetrieverWithOracle(document_store=store, mode="default")

    result = retriever.run("apple")["documents"]
    assert result[0].score > 0  # type: ignore
    assert result[0].id == "a"

    result = retriever.run("banana", filters=get_filter("b"))["documents"]
    assert len(result) == 1
    assert result[0].id == "b"

    result = retriever.run("cranberry", filters=get_filter("x"))["documents"]
    assert len(result) == 0


def test_oracle_mode():
    # Should ignore query and always return documents that match the filter condition
    retriever = BM25RetrieverWithOracle(document_store=store, mode="oracle")

    result = retriever.run("apple", filters=get_filter("a"))["documents"]
    assert len(result) == 1
    assert result[0].id == "a"
    assert result[0].score == 999999  # type: ignore

    result = retriever.run("apple", filters=get_filter("b"))["documents"]
    assert len(result) == 1
    assert result[0].id == "b"
    assert result[0].score == 999999  # type: ignore

    result = retriever.run("apple", filters=get_filter("x"))["documents"]
    assert len(result) == 0

    result = retriever.run("apple", filters=None)["documents"]
    assert len(result) == 0


def test_random_mode():
    retriever = BM25RetrieverWithOracle(document_store=store, mode="random")
    result = retriever.run("apple", top_k=1)["documents"]
    assert len(result) == 1
    result = retriever.run("apple", top_k=2)["documents"]
    assert len(result) == 2
    result = retriever.run("apple", top_k=100)["documents"]
    assert len(result) == store.count_documents()
    scores = [doc.score for doc in result]
    assert all(doc.score > 0 for doc in result)  # type: ignore
    assert scores == list(sorted(scores, reverse=True))  # type: ignore


def test_oracle_related():
    # get oracle documents, then retrieve with query, filter duplicates
    retriever = BM25RetrieverWithOracle(document_store=store, mode="oracle_related")

    result = retriever.run("banana", filters=get_filter("a"), top_k=2)["documents"]
    assert len(result) == 2
    assert result[0].id == "a"
    assert result[1].id == "b"

    result = retriever.run("apple", filters=get_filter("a"), top_k=2)["documents"]
    assert len(result) == 2
    assert result[0].id == "a"
    assert result[1].id in ["b", "c", "d"]  # cannot tell which takes precedence

    result = retriever.run("banana", filters=get_filter("a"), top_k=5)["documents"]
    assert len(result) == 4
    assert result[0].id == "a"
    assert result[1].id == "b"
    assert set(doc.id for doc in result[2:]) == set(["c", "d"])

    filters = {
        "operator": "OR",
        "conditions": [
            get_filter("a"),
            get_filter("b"),
        ],
    }
    result = retriever.run("cranberry", filters=filters, top_k=5)["documents"]
    assert len(result) == 4
    assert result[0].id == "a"
    assert result[1].id == "b"
    assert result[2].id == "c"
    assert result[3].id == "d"


def test_oracle_random():
    retriever = BM25RetrieverWithOracle(document_store=store, mode="oracle_random")

    result = retriever.run("banana", filters=get_filter("a"), top_k=2)["documents"]
    assert len(result) == 2
    assert result[0].id == "a"
    assert result[1].id in ["b", "c", "d"]

    result = retriever.run("apple", filters=get_filter("a"), top_k=2)["documents"]
    assert len(result) == 2
    assert result[0].id == "a"
    assert result[1].id in ["b", "c", "d"]

    result = retriever.run("apple", filters=get_filter("a"), top_k=3)["documents"]
    assert len(result) == 3
    assert result[0].id == "a"
    assert len(set(doc.id for doc in result[1:])) == 2

    result = retriever.run("banana", filters=get_filter("a"), top_k=5)["documents"]
    assert len(result) == store.count_documents()
    assert result[0].id == "a"
    assert len(set(doc.id for doc in result[1:])) == 3


def test_invalid_mode():
    with pytest.raises(ValueError):
        BM25RetrieverWithOracle(document_store=store, mode="unknown")
