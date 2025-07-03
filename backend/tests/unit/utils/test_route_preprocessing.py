from marcel.utils.route_preprocessing import (
    detect_non_answer,
    find_links,
    format_known_links,
    format_links,
)


def test_find_links():
    text = "This is the [link description][1] and another [link][1999] and an [incorrect link][2]."
    assert find_links(text) == [1, 1999, 2]


def test_format_links():
    links = {1: "http://foo.com/", 1999: "http://bar.com"}
    assert format_links(links) == "[1]: http://foo.com/\n[1999]: http://bar.com"


def test_format_known_links():
    text = "This is the [link description][1] and another [link][1999] and an [incorrect link][2]."
    links = {
        1: "http://foo.com/",
        2: "http://bar.com",
        3: "http://unreferenced.com",
    }

    text_formatted, links_formatted = format_known_links(text, links)
    assert text_formatted == f"{text}\n\n{links_formatted}"
    assert links_formatted == "[1]: http://foo.com/\n[2]: http://bar.com"

    text = "This text has no links."
    text_formatted, links_formatted = format_known_links(text, links)
    assert text_formatted == "This text has no links."
    assert links_formatted == ""


def test_detect_non_answer():
    assert detect_non_answer("Unfortunately, I do not have any knowledge about this.")
    assert detect_non_answer("I don't have any information on that topic.")
    assert detect_non_answer("The text doesn't provide information on this issue.")
    assert detect_non_answer("I do not have this information you are asking for.")
    assert detect_non_answer(
        "According to the sources, the documents do not specify anything."
    )

    assert not detect_non_answer("Here is the detailed information you requested.")
    assert not detect_non_answer("I found some relevant data in the document.")
    assert not detect_non_answer(
        "Unfortunately, this is not clear, but some parts are specified."
    )
    assert not detect_non_answer("This is an answer with partial information.")
    assert not detect_non_answer("")
    assert not detect_non_answer(
        "I don't have any information on that topic. However, I can tell you about a couple of options: There are emergency accommodation options where you can stay in a common room with 3 to 8 people ..."
    )
