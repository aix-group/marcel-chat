import random
import re
from typing import Dict, List

from haystack import (
    Document,
    component,
)


@component
class MostRelevantFirstReranker:
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        documents = list(sorted(documents, key=lambda doc: doc.score, reverse=True))
        return {"documents": documents}


@component
class MostRelevantLastReranker:
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        documents = list(sorted(documents, key=lambda doc: doc.score, reverse=False))
        return {"documents": documents}


@component
class RandomReranker:
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        documents = list(documents)
        random.shuffle(documents)
        return {"documents": documents}


def clean_unlinked_references(content: str, matched: str):
    """
    This function removes invalid or unreferenced link references from the content of a document.

    ### Functionality:
    - Matches and processes the following patterns in the content:
    - `[forward][60]`
    - `![][60]`
    - For complex links like `[ ![][60] link ][55]`, it simplifies and retains valid parts, resulting in `[ link ][55]`.

    """
    match_unlinked = re.findall(rf"(?:!\[\]|\[[^\[\]]+\])\{matched}", content)
    for match_cur in match_unlinked:
        content = content.replace(match_cur, "")
    return content


@component
class ContentLinkNormalizer:
    """
    ContentLinkNormalizer is a component designed to normalize and process links within a list of documents.

    ### Functionality:
    - Extracts and processes links from the `meta["links"]` attribute of each document.
    - Creates a mapping of links to new indices, ensuring a consistent and cleaned-up link structure.
    - Updates the content of each document, replacing outdated link references with new ones and removing unreferenced links.
    - Cleans the content by removing specific phrases and standardizing link formats.
    - Updates the `meta["links"]` attribute of each document to reflect the new link structure.

    ### Notes:
    - Documents without a `meta["links"]` attribute are skipped.
    - Link references in the content are updated based on the processed link indices.
    - Specific phrases such as "Inhalt ausklappen" and "Alle Elemente ausklappen" are removed from the content for better readability.
    - Unreferenced links in the content are identified and removed.
    """

    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]):
        global_links = {}
        for document in documents:
            if "links" not in document.meta:
                continue
            global_links.update(document.meta["links"])

        reordering = {key: i for i, key in enumerate(global_links)}

        result = []
        for document in documents:
            doc_fields = document.to_dict()
            content = doc_fields["content"]
            links = {}

            for matched in re.findall(r"\[\d+\]", content):
                matched = int(matched[1:-1])
                if matched not in reordering:
                    content = clean_unlinked_references(content, f"[{matched}]")
                else:
                    content = content.replace(
                        f"[{matched}]", f"[_{reordering[matched]}]"
                    )
                    links[reordering[matched]] = global_links[matched]

            content = content.replace("Inhalt ausklappen", "")
            content = content.replace("Inhalt einklappen", "")
            content = content.replace("Alle Elemente ausklappen", "")
            content = content.replace("Alle Elemente einklappen", "")
            content = re.sub(r"\[_(\d+)\]", r"[\1]", content)
            doc_fields["content"] = content
            doc_fields["links"] = links
            new_doc = Document.from_dict(doc_fields)
            result.append(new_doc)

        return {"documents": result}
