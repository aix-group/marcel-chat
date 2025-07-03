import re
from typing import Dict, List, Tuple


def find_links(text: str) -> List[int]:
    """Finds labels of all reference-style links in a Markdown fromatted text.

    Parameters
    ----------
    text : str
        The input text containing links in the format `[description][label]`. Assumes that labels are integers.

    Returns
    -------
    labels: List[int]
        The list of labels.
    """

    link_pattern = re.compile(r"\[.*?\]\[(\d+)\]")
    matches = link_pattern.finditer(text)
    return [int(match.group(1)) for match in matches]


def format_links(links: Dict[int, str]) -> str:
    """Formats links in Markdown reference-style.

    See: https://www.markdownguide.org/basic-syntax/#formatting-the-second-part-of-the-link

    Parameters
    ----------
    links : Dict[int, str]
        A map of label to url.

    Returns
    -------
    str
        A string with `[label]: url` entries separated by newlines.
    """
    return "\n".join(f"[{label}]: {url}" for label, url in links.items())


def format_known_links(text: str, links: Dict[int, str]) -> Tuple[str, str]:
    """Adds Markdown reference-style links to the given text based on the referenced labels.

    Only links which are "known" (i.e., exist in the `links` dictionary) are appended to the text. The motivation is that text may have dangling links which we do not have any definition for. Handling this correctly is left for the client.
    """
    referenced_labels = find_links(text)
    known_links = {label: links[label] for label in referenced_labels if label in links}
    formatted_links = format_links(known_links)
    return f"{text}\n\n{formatted_links}".strip(), formatted_links


_non_answer_pattern = re.compile(
    r"(I (do not|don't) have (any )?(knowledge|information)|"
    r"The text doesn't provide information|"
    r"I do not have this information|"
    r"the documents do not specify)",
    re.IGNORECASE,
)


def detect_non_answer(text: str) -> bool:
    return _non_answer_pattern.search(text) is not None and len(text.split(" ")) < 30
