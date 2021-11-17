import pytest

from aurweb import config, templates
from aurweb.templates import register_filter, register_function
from aurweb.testing.requests import Request


@register_filter("func")
def func():
    pass


@register_function("function")
def function():
    pass


def test_register_filter_exists_key_error():
    """ Most instances of register_filter are tested through module
    imports or template renders, so we only test failures here. """
    with pytest.raises(KeyError):
        @register_filter("func")
        def some_func():
            pass


def test_register_function_exists_key_error():
    """ Most instances of register_filter are tested through module
    imports or template renders, so we only test failures here. """
    with pytest.raises(KeyError):
        @register_function("function")
        def some_func():
            pass


def test_commit_hash():
    # Hashes we'll use for this test. long_commit_hash should be
    # shortened to commit_hash for rendering.
    commit_hash = "abcdefg"
    long_commit_hash = commit_hash + "1234567"

    def config_get_with_fallback(section: str, option: str,
                                 fallback: str = None) -> str:
        if section == "devel" and option == "commit_hash":
            return long_commit_hash
        return config.original_get_with_fallback(section, option, fallback)

    # Fake config.get_with_fallback.
    config.original_get_with_fallback = config.get_with_fallback
    config.get_with_fallback = config_get_with_fallback

    request = Request()
    context = templates.make_context(request, "Test Context")
    render = templates.render_raw_template(request, "index.html", context)

    # We've faked config.get_with_fallback to return a "valid" commit_hash
    # when queried. Test that the expected render occurs.
    commit_url = config.get("devel", "commit_url")
    expected = commit_url % commit_hash
    assert expected in render
    assert f"HEAD@{commit_hash}" in render
    assert long_commit_hash not in render

    # Restore config.get_with_fallback.
    config.get_with_fallback = config.original_get_with_fallback
    config.original_get_with_fallback = None

    # Now, we no longer fake the commit_hash option: no commit
    # is displayed in the footer. Assert this expectation.
    context = templates.make_context(request, "Test Context")
    render = templates.render_raw_template(request, "index.html", context)
    assert commit_hash not in render