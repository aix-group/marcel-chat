from scraper.spiders.university_spider import (
    find_content,
    find_favicon,
    find_title,
    get_domain,
    get_domain_with_schema,
    replace_domain,
    resolve_link,
)


def test_url_to_domain():
    assert get_domain("https://www.uni-marburg.de/en/") == "uni-marburg.de"
    assert get_domain("https://uni-marburg.de/en/") == "uni-marburg.de"
    assert get_domain("https://www.uni-marburg.de") == "uni-marburg.de"
    assert get_domain("https://uni-marburg.de/en/") == "uni-marburg.de"
    assert get_domain("https://uni-marburg.de") == "uni-marburg.de"


def test_extract_content():
    # find tag with id=content
    tag = find_content(
        '<html><body><main><div id="content">Hello World.</div></main></body></html>',
        "example.com",
    )
    assert tag
    assert tag.name == "div"
    assert tag.get_text() == "Hello World."

    # fallback to main
    tag = find_content(
        "<html><body><main><div>Hello World.</div></main></body></html>",
        "example.com",
    )
    assert tag
    assert tag.name == "main"
    assert tag.get_text() == "Hello World."

    # fallback to body
    tag = find_content(
        "<html><body><div>Hello World.</div></body></html>",
        "example.com",
    )
    assert tag
    assert tag.name == "body"
    assert tag.get_text() == "Hello World."

    # if no body, return None
    tag = find_content(
        "<html></html>",
        "example.com",
    )
    assert not tag


def test_replace_domain():
    domain_map = {"foo.com": "bar.com", "www.foo.com": "www.bar.com"}

    def replace(url):  # shorthand
        return replace_domain(url, domain_map)

    assert replace("//www.bar.com/") == "//www.bar.com/"
    assert replace("//bar.com/test/") == "//bar.com/test/"
    assert replace("//foo.com/test/") == "//bar.com/test/"
    assert replace("//www.foo.com/") == "//www.bar.com/"
    assert replace("//www.foo.com") == "//www.bar.com"
    assert replace("//www.foo.com/#test") == "//www.bar.com/#test"


def test_find_title():
    html = "<html><head><title>Page Title</title></head><body><main><div>Hello World.</div></main></body></html>"
    assert find_title(html) == "Page Title"
    html = "<html><head></head><body><main><div>Hello World.</div></main></body></html>"
    assert not find_title(html)


def test_find_favicon():
    html = '<html><head><link rel="icon" href="favicon.ico" /><title>Page Title</title></head><body><main><div>Hello World.</div></main></body></html>'
    assert find_favicon(html) == "favicon.ico"
    html = '<html><head><link rel="shortcut icon" href="favicon.ico" /><title>Page Title</title></head><body><main><div>Hello World.</div></main></body></html>'
    assert find_favicon(html) == "favicon.ico"
    html = "<html><head><title>Page Title</title></head><body><main><div>Hello World.</div></main></body></html>"
    assert not find_favicon(html)


def test_resolve_url():
    base = "http://uni-marburg.de"
    link = "favicon.ico"
    expected = "http://uni-marburg.de/favicon.ico"
    assert resolve_link(base, link) == expected

    base = "http://uni-marburg.de"
    link = "/favicon.ico"
    expected = "http://uni-marburg.de/favicon.ico"
    assert resolve_link(base, link) == expected

    base = "http://uni-marburg.de"
    link = "/bar/favicon.ico?test"
    expected = "http://uni-marburg.de/bar/favicon.ico?test"
    assert resolve_link(base, link) == expected

    base = "http://uni-marburg.de"
    link = "http://uni-marburg.de/bar/favicon.ico?test"
    expected = "http://uni-marburg.de/bar/favicon.ico?test"
    assert resolve_link(base, link) == expected

    base = "uni-marburg.de"
    link = "favicon.ico"
    expected = "http://uni-marburg.de/favicon.ico"
    assert resolve_link(base, link) == expected, (
        "should assume http:// default scheme if missing"
    )


def test_get_domain_with_schema():
    url = "https://uni-marburg.de/foo/bar"
    expected = "https://uni-marburg.de"
    assert get_domain_with_schema(url) == expected
