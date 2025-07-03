import json
import textwrap
from pathlib import Path

from marcel.experiments.data_loader import (
    clean_bolded_headers,
    clean_bulleted_headers,
    clean_collapsibles,
    clean_content,
    clean_empty_headers,
    clean_url,
    extract_links,
    load_documents,
    load_faqs,
)


def test_clean_url():
    # fmt: off
    expected = "uni-marburg.de/en/studying/degree-programs/sciences/datasciencems"
    case1 = "https://www.uni-marburg.de/en/studying/degree-programs/sciences/datasciencems"
    case2 = "https://www.uni-marburg.de/en/studying/degree-programs/sciences/datasciencems/"
    assert clean_url(case1) == expected
    assert clean_url(case2) == expected

    expected = "uni-marburg.de/en/studying/degree-programs/sciences/datasciencems?a=b&foo=bar"
    case1 = "https://www.uni-marburg.de/en/studying/degree-programs/sciences/datasciencems?foo=bar&a=b"
    case2 = "http://www.uni-marburg.de/en/studying/degree-programs/sciences/datasciencems?a=b&foo=bar"
    case3 = "www.uni-marburg.de/en/studying/degree-programs/sciences/datasciencems?a=b&foo=bar"
    case4 = "uni-marburg.de/en/studying/degree-programs/sciences/datasciencems?a=b&foo=bar"
    assert clean_url(case1) == expected
    assert clean_url(case2) == expected
    assert clean_url(case3) == expected
    assert clean_url(case4) == expected
    # fmt: on


CLEAN_CONTENT_INPUT = """
###### main content

# Data science


- Test
- Another test

Where to find more? [here

](example.com)

Where to find even more? [here

][1]

[1]: example.com
"""

CLEAN_CONTENT_EXPECTED = """# Data science

- Test
- Another test

Where to find more? [here](example.com)

Where to find even more? [here][1]"""


def test_clean_content():
    assert clean_content(CLEAN_CONTENT_INPUT) == CLEAN_CONTENT_EXPECTED


def test_clean_collapsible_sections():
    text = textwrap.dedent(
        """
        Alle Elemente ausklappen Alle Elemente einklappen

        * ### [Inhalt ausklappen Inhalt einklappen Final grade][28]

        Up to 55 eligibility points are awarded for the final grade or the provisional final grade according to the following scheme:
        """
    )
    expected = textwrap.dedent(
        """
        * ### [Final grade][28]

        Up to 55 eligibility points are awarded for the final grade or the provisional final grade according to the following scheme:
        """
    )

    assert clean_collapsibles(text).strip() == expected.strip()


def test_clean_bulleted_headers():
    text = textwrap.dedent(
        """
        * ### This is a header

        And some content below it

        * # Another header

        And some content below it
        And some content below it
        And some content below it

        - # Yet another one
            * #### Final header
        """
    )
    expected = textwrap.dedent(
        """
        ### This is a header

        And some content below it

        # Another header

        And some content below it
        And some content below it
        And some content below it

        # Yet another one
        #### Final header
        """
    )

    assert clean_bulleted_headers(text).strip() == expected.strip()


def test_clean_bolded_headers():
    text = textwrap.dedent(
        """
        ## This is a header
        Text

        ### **this one is bold?**

        This is a **normal bold**.

           # **another one**

        here is text
        """
    )
    expected = textwrap.dedent(
        """
        ## This is a header
        Text

        ### this one is bold?

        This is a **normal bold**.

           # another one

        here is text
        """
    )
    assert clean_bolded_headers(text).strip() == expected.strip()


def test_clean_empty_headers():
    text = textwrap.dedent(
        """
        ## This is a header
        Text

        ###

            ##

        # **another one**
        here is text

        #
        Some text
        """
    )
    expected = textwrap.dedent(
        """
        ## This is a header
        Text





        # **another one**
        here is text


        Some text
        """
    )
    assert clean_empty_headers(text).strip() == expected.strip()


def test_extract_links():
    text = """
    [1]: http://example.com
    [2]: https://example.com
    [3]: foo@example.com

    bar@example.com

    [4]: another@example.com
    [5]: javascript:;

    [10000]:
    """

    assert extract_links(text) == {
        1: "http://example.com",
        2: "https://example.com",
        3: "foo@example.com",
        4: "another@example.com",
    }

    text = """example.com [5]: https://example.com/image@@images"""

    assert extract_links(text) == {}


def test_load_documents(tmpdir):
    docs = [
        {
            "url": "http://example.com",
            "content": "This is some test content.",
            "title": "Example",
            "favicon": "icon.ico",
            "og": {"og:title": "Example"},
        },
        {
            "url": "http://test.com",
            "content": "Content about test.",
            "title": "Test",
            "favicon": "icon.ico",
            "og": {"og:title": "Test"},
        },
        {
            "url": "http://website.com",
            "content": "Another website.",
            "title": "Website",
            "favicon": "icon.ico",
            "og": {"og:title": "Website"},
        },
    ]

    data_path = Path(tmpdir) / "documents.jsonl"
    with open(data_path, "w") as fout:
        for doc in docs:
            fout.write(json.dumps(doc) + "\n")

    parsed = load_documents(data_path)
    assert len(parsed) == len(docs)
    assert parsed[0].content == "This is some test content."
    assert parsed[0].meta["url"] == "example.com"
    assert parsed[0].meta["og:title"] == "Example"
    assert parsed[0].meta["fingerprint"] is not None


def test_load_faqs(tmpdir):
    faqs = [
        {
            "id": "faq-0000-0",
            "question": "What is x?",
            "sources": ["https://example.com"],
        },
        {
            "id": "faq-0000-1",
            "question": "What is this x again?",
            "sources": ["https://example.com"],
        },
        {
            "id": "faq-0001-0",
            "question": "What is y?",
            "sources": ["https://test.com"],
        },
        {
            "id": "faq-0002-0",
            "question": "This is a question without a source?",
            "sources": [],
        },
    ]

    data_path = Path(tmpdir) / "faqs.json"
    with open(data_path, "w") as fout:
        json.dump(faqs, fout)

    data = load_faqs(data_path)
    assert len(data) == 2
    assert data[0].content == "What is x?"
    assert data[0].meta["sources"] == ["example.com"]

    assert data[1].content == "What is y?"
    assert data[1].meta["sources"] == ["test.com"]
