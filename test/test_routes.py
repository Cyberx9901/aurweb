import re
import urllib.parse

from http import HTTPStatus

import lxml.etree
import pytest

from fastapi.testclient import TestClient

from aurweb import db
from aurweb.asgi import app
from aurweb.models.account_type import AccountType
from aurweb.models.user import User
from aurweb.testing import setup_test_db
from aurweb.testing.requests import Request

user = client = None


@pytest.fixture(autouse=True)
def setup():
    global user, client

    setup_test_db("Users", "Sessions")

    account_type = db.query(AccountType,
                            AccountType.AccountType == "User").first()

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountType=account_type)

    client = TestClient(app)


def test_index():
    """ Test the index route at '/'. """
    # Use `with` to trigger FastAPI app events.
    with client as req:
        response = req.get("/")
    assert response.status_code == int(HTTPStatus.OK)


def test_index_security_headers():
    """ Check for the existence of CSP, XCTO, XFO and RP security headers.

    CSP: Content-Security-Policy
    XCTO: X-Content-Type-Options
    RP: Referrer-Policy
    XFO: X-Frame-Options
    """
    # Use `with` to trigger FastAPI app events.
    with client as req:
        response = req.get("/")
    assert response.status_code == int(HTTPStatus.OK)
    assert response.headers.get("Content-Security-Policy") is not None
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "same-origin"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"


def test_favicon():
    """ Test the favicon route at '/favicon.ico'. """
    response1 = client.get("/static/images/favicon.ico")
    response2 = client.get("/favicon.ico")
    assert response1.status_code == int(HTTPStatus.OK)
    assert response1.content == response2.content


def test_language():
    """ Test the language post route as a guest user. """
    post_data = {
        "set_lang": "de",
        "next": "/"
    }
    with client as req:
        response = req.post("/language", data=post_data)
    assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_language_invalid_next():
    """ Test an invalid next route at '/language'. """
    post_data = {
        "set_lang": "de",
        "next": "https://evil.net"
    }
    with client as req:
        response = req.post("/language", data=post_data)
    assert response.status_code == int(HTTPStatus.BAD_REQUEST)


def test_user_language():
    """ Test the language post route as an authenticated user. """
    post_data = {
        "set_lang": "de",
        "next": "/"
    }

    sid = user.login(Request(), "testPassword")
    assert sid is not None

    with client as req:
        response = req.post("/language", data=post_data,
                            cookies={"AURSID": sid})
    assert response.status_code == int(HTTPStatus.SEE_OTHER)
    assert user.LangPreference == "de"


def test_language_query_params():
    """ Test the language post route with query params. """
    next = urllib.parse.quote_plus("/")
    post_data = {
        "set_lang": "de",
        "next": "/",
        "q": f"next={next}"
    }
    q = post_data.get("q")
    with client as req:
        response = req.post("/language", data=post_data)
        assert response.headers.get("location") == f"/?{q}"
    assert response.status_code == int(HTTPStatus.SEE_OTHER)


def test_error_messages():
    response1 = client.get("/thisroutedoesnotexist")
    response2 = client.get("/raisefivethree")
    assert response1.status_code == int(HTTPStatus.NOT_FOUND)
    assert response2.status_code == int(HTTPStatus.SERVICE_UNAVAILABLE)


def test_nonce_csp():
    with client as request:
        response = request.get("/")
    data = response.headers.get("Content-Security-Policy")
    nonce = next(field for field in data.split("; ") if "nonce" in field)
    match = re.match(r"^script-src .*'nonce-([a-fA-F0-9]{8})' .*$", nonce)
    nonce = match.group(1)
    assert nonce is not None and len(nonce) == 8

    parser = lxml.etree.HTMLParser(recover=True)
    root = lxml.etree.fromstring(response.text, parser=parser)

    nonce_verified = False
    scripts = root.xpath("//script")
    for script in scripts:
        if script.text is not None:
            assert "nonce" in script.keys()
            if not (nonce_verified := (script.get("nonce") == nonce)):
                break
    assert nonce_verified is True


def test_id_redirect():
    with client as request:
        response = request.get("/", params={
            "id": "test",  # This param will be rewritten into Location.
            "key": "value",  # Test that this param persists.
            "key2": "value2"  # And this one.
        }, allow_redirects=False)
    assert response.headers.get("location") == "/test?key=value&key2=value2"
