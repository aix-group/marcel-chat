import json
import logging
import re
from hashlib import sha256
from typing import List

from haystack import Document
from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)


def clean_url(u):
    u = canonicalize_url(u)
    if u.startswith("http://"):
        u = u[7:]
    if u.startswith("https://"):
        u = u[8:]
    if u.startswith("www."):
        u = u[4:]
    if u.endswith("/"):
        u = u[:-1]
    return u


def clean_content(content: str):
    # Remove links
    content = re.sub(r"\[\d+\]: .*", "", content)

    # Remove markup element often at top of page
    content = re.sub(r"###### Main Content", "", content, flags=re.IGNORECASE)

    content = clean_collapsibles(content)
    content = clean_bulleted_headers(content)
    content = clean_bolded_headers(content)
    content = clean_empty_headers(content)

    # Replace multiple newlines (with optional trailing whitespace) with a single newline
    # 1) Remove trailing whitespace from each line
    content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)
    # 2) Collapse multiple consecutive newlines into two newlines
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Remove newlines within markdown link descriptions
    content = re.sub(r"\n\s*\n*(\s*\])", r"\1", content)
    content = content.strip()
    return content


def clean_collapsibles(content: str):
    content = re.sub(
        "Inhalt ausklappen Inhalt einklappen ", "", content, flags=re.IGNORECASE
    )
    content = re.sub(
        "Alle Elemente ausklappen Alle Elemente einklappen",
        "",
        content,
        flags=re.IGNORECASE,
    )
    return content


def clean_bulleted_headers(content: str):
    return re.sub(r"^[^\S\n]*[\*-][^\S\n]*#", "#", content, flags=re.MULTILINE)


BOLD_HEADER_PATTERN = re.compile(
    r"""
    ^                  # Start of line
    ([^\S\n]*\#+)      # Group 1: leading space (not newlines) and one or more '#'
    [^\S\n]+           # At least one space after the hash
    \*\*               # Opening bold (**)
    (.*?)              # Group 2: header content (non-greedy)
    \*\*               # Closing bold (**)
    $                  # End of line
    """,
    re.MULTILINE | re.VERBOSE,
)


def clean_bolded_headers(content: str):
    return BOLD_HEADER_PATTERN.sub(r"\1 \2", content)


def clean_empty_headers(text: str) -> str:
    def is_empty_header(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith("#"):
            return False
        # Remove leading #'s and whitespace
        content = stripped.lstrip("#").strip()
        # Consider it empty if nothing remains or only formatting like bold/italic
        return content == ""

    lines = text.splitlines()
    cleaned_lines = ["" if is_empty_header(line) else line for line in lines]
    return "\n".join(cleaned_lines)


def extract_links(content):
    links = {}
    for link in re.findall(r"\[\d+\]: .+", content):
        if "javascript" not in link and "@@images" not in link:
            number, link = link.split()[:2]
            number = int(number[1:-2])
            links[number] = link
    return links


def load_raw_docs(data_path):
    docs = []

    with open(data_path, "r") as fin:
        for line in fin:
            try:
                doc = json.loads(line)  # Parse each line as a JSON object
                docs.append(doc)
            except json.JSONDecodeError:
                logger.exception("Error decoding JSON")

    return docs


def fingerprint(data):
    return sha256(str(data).encode("utf-8")).hexdigest()


def load_documents(data_path) -> List[Document]:
    raw_docs = load_raw_docs(data_path)
    docs = []
    for doc in raw_docs:
        data = {
            "content": clean_content(doc["content"]),
            "url": clean_url(doc["url"]),
            "url_raw": doc["url"],
            "title": doc.get("title", doc["url"]),
            "favicon": doc.get("favicon", ""),
            "links": extract_links(doc["content"]),
            **doc["og"],
        }
        data["fingerprint"] = fingerprint(data)
        doc = Document.from_dict(data)
        docs.append(doc)
    return docs


def load_queries(path, skip_without_sources=False):
    with open(path) as fin:
        queries = json.load(fin)

    for query in queries:
        query["sources"] = [clean_url(url) for url in query["sources"]]

    if skip_without_sources:
        queries = [q for q in queries if len(q["sources"]) > 0]

    return queries


def load_faqs(faq_path) -> List[Document]:
    with open(faq_path) as fin:
        raw_faqs = json.load(fin)

    faqs = []
    for question in raw_faqs:
        # in 2024 evaluation data we had <faq>-<id>-<paraphrase_id>
        # in more recent dumps we don't have a paraphrase_id
        parts = question["id"].split("-")
        is_paraphrase = len(parts) == 3 and int(parts[2]) > 0
        if is_paraphrase:
            logger.debug("Skipping %s (reason: paraphrase)", question["id"])
            continue

        empty_sources = len(question["sources"]) <= 0
        if empty_sources:
            logger.debug("Skipping %s (reason: empty sources)", question["id"])
            continue

        doc = Document(
            content=question["question"],
            meta={"sources": [clean_url(url) for url in question["sources"]]},
        )
        faqs.append(doc)
    return faqs
