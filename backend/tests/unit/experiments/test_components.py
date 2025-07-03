from haystack import Document

from marcel.experiments.components import (
    ContentLinkNormalizer,
    MostRelevantFirstReranker,
    MostRelevantLastReranker,
    RandomReranker,
    clean_unlinked_references,
)


def test_most_relevant_first_reranker():
    docs = [
        Document(score=2),
        Document(score=1),
        Document(score=3),
    ]
    reranker = MostRelevantFirstReranker()
    result = reranker.run(documents=docs)["documents"]
    scores = [doc.score for doc in result]
    assert scores == [3, 2, 1]


def test_most_relevant_last_reranker():
    docs = [
        Document(score=2),
        Document(score=1),
        Document(score=3),
    ]
    reranker = MostRelevantLastReranker()
    result = reranker.run(documents=docs)["documents"]
    scores = [doc.score for doc in result]
    assert scores == [1, 2, 3]


def test_random_reranker():
    docs = [
        Document(score=2),
        Document(score=1),
        Document(score=3),
    ]
    reranker = RandomReranker()
    result = reranker.run(documents=docs)["documents"]
    scores = [doc.score for doc in result]
    assert set(scores) == set([1, 2, 3])


def test_content_link_normalizer():
    docs = [
        Document(
            id="1",
            content="[ ![][3] link 1][1] This is a test content with a [reference ][1] and [reference ][2]. Inhalt ausklappen",
            meta={
                "links": {
                    1: "https://example.com/link1",
                    2: "https://example.com/link2",
                }
            },
        ),
        Document(
            id="2",
            content="Another doc with [reference ][2] and [reference ][999] and [ reference ][1000] [test][25]. Alle Elemente ausklappen",
            meta={
                "links": {
                    2: "https://example.com/link2",
                    999: "https://example.com/link999",
                }
            },
        ),
    ]

    normalizer = ContentLinkNormalizer()
    output = normalizer.run(docs)

    (doc1, doc2) = output["documents"]

    assert "https://example.com/link1" in doc1.meta["links"].values()
    assert "https://example.com/link2" in doc1.meta["links"].values()
    assert len(doc1.meta["links"]) == 2
    assert (
        doc1.content
        == "[  link 1][0] This is a test content with a [reference ][0] and [reference ][1]. "
    ), doc1.content
    assert (
        doc2.content == "Another doc with [reference ][1] and [reference ][2] and  . "
    ), doc2.content
    assert len(doc2.meta["links"]) == 2

    doc1_link_to_number = {link: key for key, link in doc1.meta["links"].items()}
    doc2_link_to_number = {link: key for key, link in doc2.meta["links"].items()}

    doc1_link2_number = doc1_link_to_number["https://example.com/link2"]
    doc2_link2_number = doc2_link_to_number["https://example.com/link2"]

    assert doc1_link2_number is not None, (
        "doc1 should contain a reference number for link2"
    )
    assert doc2_link2_number is not None, (
        "doc2 should contain a reference number for link2"
    )
    assert doc1_link2_number == doc2_link2_number, (
        f"link2 has different reference numbers: doc1={doc1_link2_number}, doc2={doc2_link2_number}"
    )


def test_clean_unlinked_references():
    content = "[ ![][51] ][90]"
    matched = "[51]"
    assert clean_unlinked_references(content, matched) == "[  ][90]"

    content = "[Backward][60]"
    matched = "[60]"
    assert clean_unlinked_references(content, matched) == ""

    content = "[ Forward ][60]"
    matched = "[60]"
    assert clean_unlinked_references(content, matched) == ""

    content = "[Forward ][60]"
    matched = "[60]"
    assert clean_unlinked_references(content, matched) == ""

    content = "[ Forward][60]"
    matched = "[60]"
    assert clean_unlinked_references(content, matched) == ""

    content = "[            Forward                               ][60]"
    matched = "[60]"
    assert clean_unlinked_references(content, matched) == ""
