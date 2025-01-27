import logging
import os
import ssl

from json import dumps as json_dumps
from json import loads as json_loads
from urllib.parse import urlparse

import pytest

from sanic import Blueprint, Sanic
from sanic.exceptions import ServerError
from sanic.request import DEFAULT_HTTP_CONTENT_TYPE, RequestParameters
from sanic.response import json, text
from sanic.testing import ASGI_HOST, HOST, PORT


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #


def test_sync(app):
    @app.route("/")
    def handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert response.text == "Hello"


@pytest.mark.asyncio
async def test_sync_asgi(app):
    @app.route("/")
    def handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert response.text == "Hello"


def test_ip(app):
    @app.route("/")
    def handler(request):
        return text("{}".format(request.ip))

    request, response = app.test_client.get("/")

    assert response.text == "127.0.0.1"


@pytest.mark.asyncio
async def test_ip_asgi(app):
    @app.route("/")
    def handler(request):
        return text("{}".format(request.ip))

    request, response = await app.asgi_client.get("/")

    assert response.text == "mockserver"


def test_text(app):
    @app.route("/")
    async def handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert response.text == "Hello"


@pytest.mark.asyncio
async def test_text_asgi(app):
    @app.route("/")
    async def handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert response.text == "Hello"


def test_headers(app):
    @app.route("/")
    async def handler(request):
        headers = {"spam": "great"}
        return text("Hello", headers=headers)

    request, response = app.test_client.get("/")

    assert response.headers.get("spam") == "great"


@pytest.mark.asyncio
async def test_headers_asgi(app):
    @app.route("/")
    async def handler(request):
        headers = {"spam": "great"}
        return text("Hello", headers=headers)

    request, response = await app.asgi_client.get("/")

    assert response.headers.get("spam") == "great"


def test_non_str_headers(app):
    @app.route("/")
    async def handler(request):
        headers = {"answer": 42}
        return text("Hello", headers=headers)

    request, response = app.test_client.get("/")

    assert response.headers.get("answer") == "42"


@pytest.mark.asyncio
async def test_non_str_headers_asgi(app):
    @app.route("/")
    async def handler(request):
        headers = {"answer": 42}
        return text("Hello", headers=headers)

    request, response = await app.asgi_client.get("/")

    assert response.headers.get("answer") == "42"


def test_invalid_response(app):
    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text("Internal Server Error.", 500)

    @app.route("/")
    async def handler(request):
        return "This should fail"

    request, response = app.test_client.get("/")
    assert response.status == 500
    assert response.text == "Internal Server Error."


@pytest.mark.asyncio
async def test_invalid_response_asgi(app):
    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text("Internal Server Error.", 500)

    @app.route("/")
    async def handler(request):
        return "This should fail"

    request, response = await app.asgi_client.get("/")
    assert response.status == 500
    assert response.text == "Internal Server Error."


def test_json(app):
    @app.route("/")
    async def handler(request):
        return json({"test": True})

    request, response = app.test_client.get("/")

    results = json_loads(response.text)

    assert results.get("test") is True


@pytest.mark.asyncio
async def test_json_asgi(app):
    @app.route("/")
    async def handler(request):
        return json({"test": True})

    request, response = await app.asgi_client.get("/")

    results = json_loads(response.text)

    assert results.get("test") is True


def test_empty_json(app):
    @app.route("/")
    async def handler(request):
        assert request.json is None
        return json(request.json)

    request, response = app.test_client.get("/")
    assert response.status == 200
    assert response.text == "null"


@pytest.mark.asyncio
async def test_empty_json_asgi(app):
    @app.route("/")
    async def handler(request):
        assert request.json is None
        return json(request.json)

    request, response = await app.asgi_client.get("/")
    assert response.status == 200
    assert response.text == "null"


def test_invalid_json(app):
    @app.route("/")
    async def handler(request):
        return json(request.json)

    data = "I am not json"
    request, response = app.test_client.get("/", data=data)

    assert response.status == 400


@pytest.mark.asyncio
async def test_invalid_json_asgi(app):
    @app.route("/")
    async def handler(request):
        return json(request.json)

    data = "I am not json"
    request, response = await app.asgi_client.get("/", data=data)

    assert response.status == 400


def test_query_string(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get(
        "/", params=[("test1", "1"), ("test2", "false"), ("test2", "true")]
    )

    assert request.args.get("test1") == "1"
    assert request.args.get("test2") == "false"
    assert request.args.getlist("test2") == ["false", "true"]
    assert request.args.getlist("test1") == ["1"]
    assert request.args.get("test3", default="My value") == "My value"


@pytest.mark.asyncio
async def test_query_string_asgi(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get(
        "/", params=[("test1", "1"), ("test2", "false"), ("test2", "true")]
    )

    assert request.args.get("test1") == "1"
    assert request.args.get("test2") == "false"
    assert request.args.getlist("test2") == ["false", "true"]
    assert request.args.getlist("test1") == ["1"]
    assert request.args.get("test3", default="My value") == "My value"


def test_uri_template(app):
    @app.route("/foo/<id:int>/bar/<name:[A-z]+>")
    async def handler(request, id, name):
        return text("OK")

    request, response = app.test_client.get("/foo/123/bar/baz")
    assert request.uri_template == "/foo/<id:int>/bar/<name:[A-z]+>"


@pytest.mark.asyncio
async def test_uri_template_asgi(app):
    @app.route("/foo/<id:int>/bar/<name:[A-z]+>")
    async def handler(request, id, name):
        return text("OK")

    request, response = await app.asgi_client.get("/foo/123/bar/baz")
    assert request.uri_template == "/foo/<id:int>/bar/<name:[A-z]+>"


def test_token(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    # uuid4 generated token.
    token = "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"
    headers = {
        "content-type": "application/json",
        "Authorization": "{}".format(token),
    }

    request, response = app.test_client.get("/", headers=headers)

    assert request.token == token

    token = "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"
    headers = {
        "content-type": "application/json",
        "Authorization": "Token {}".format(token),
    }

    request, response = app.test_client.get("/", headers=headers)

    assert request.token == token

    token = "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    request, response = app.test_client.get("/", headers=headers)

    assert request.token == token

    # no Authorization headers
    headers = {"content-type": "application/json"}

    request, response = app.test_client.get("/", headers=headers)

    assert request.token is None


@pytest.mark.asyncio
async def test_token_asgi(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    # uuid4 generated token.
    token = "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"
    headers = {
        "content-type": "application/json",
        "Authorization": "{}".format(token),
    }

    request, response = await app.asgi_client.get("/", headers=headers)

    assert request.token == token

    token = "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"
    headers = {
        "content-type": "application/json",
        "Authorization": "Token {}".format(token),
    }

    request, response = await app.asgi_client.get("/", headers=headers)

    assert request.token == token

    token = "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    request, response = await app.asgi_client.get("/", headers=headers)

    assert request.token == token

    # no Authorization headers
    headers = {"content-type": "application/json"}

    request, response = await app.asgi_client.get("/", headers=headers)

    assert request.token is None


def test_content_type(app):
    @app.route("/")
    async def handler(request):
        return text(request.content_type)

    request, response = app.test_client.get("/")
    assert request.content_type == DEFAULT_HTTP_CONTENT_TYPE
    assert response.text == DEFAULT_HTTP_CONTENT_TYPE

    headers = {"content-type": "application/json"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.content_type == "application/json"
    assert response.text == "application/json"


@pytest.mark.asyncio
async def test_content_type_asgi(app):
    @app.route("/")
    async def handler(request):
        return text(request.content_type)

    request, response = await app.asgi_client.get("/")
    assert request.content_type == DEFAULT_HTTP_CONTENT_TYPE
    assert response.text == DEFAULT_HTTP_CONTENT_TYPE

    headers = {"content-type": "application/json"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.content_type == "application/json"
    assert response.text == "application/json"


def test_remote_addr_with_two_proxies(app):
    app.config.PROXIES_COUNT = 2

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.text == "127.0.0.2"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.text == "127.0.0.1"

    request, response = app.test_client.get("/")
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.0.1, ,   ,,127.0.1.2"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.text == "127.0.0.1"

    headers = {
        "X-Forwarded-For": ", 127.0.2.2, ,  ,127.0.0.1, ,   ,,127.0.1.2"
    }
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.text == "127.0.0.1"


@pytest.mark.asyncio
async def test_remote_addr_with_two_proxies_asgi(app):
    app.config.PROXIES_COUNT = 2

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.text == "127.0.0.2"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.text == "127.0.0.1"

    request, response = await app.asgi_client.get("/")
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.0.1, ,   ,,127.0.1.2"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.text == "127.0.0.1"

    headers = {
        "X-Forwarded-For": ", 127.0.2.2, ,  ,127.0.0.1, ,   ,,127.0.1.2"
    }
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.text == "127.0.0.1"


def test_remote_addr_with_infinite_number_of_proxies(app):
    app.config.PROXIES_COUNT = -1

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.text == "127.0.0.2"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.1.1"
    assert response.text == "127.0.1.1"

    headers = {
        "X-Forwarded-For": "127.0.0.5, 127.0.0.4, 127.0.0.3, 127.0.0.2, 127.0.0.1"
    }
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.5"
    assert response.text == "127.0.0.5"


@pytest.mark.asyncio
async def test_remote_addr_with_infinite_number_of_proxies_asgi(app):
    app.config.PROXIES_COUNT = -1

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.text == "127.0.0.2"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.1.1"
    assert response.text == "127.0.1.1"

    headers = {
        "X-Forwarded-For": "127.0.0.5, 127.0.0.4, 127.0.0.3, 127.0.0.2, 127.0.0.1"
    }
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.5"
    assert response.text == "127.0.0.5"


def test_remote_addr_without_proxy(app):
    app.config.PROXIES_COUNT = 0

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""


@pytest.mark.asyncio
async def test_remote_addr_without_proxy_asgi(app):
    app.config.PROXIES_COUNT = 0

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""


def test_remote_addr_custom_headers(app):
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "Client-IP"
    app.config.FORWARDED_FOR_HEADER = "Forwarded"

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.1.1"
    assert response.text == "127.0.1.1"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"Client-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.text == "127.0.0.2"


@pytest.mark.asyncio
async def test_remote_addr_custom_headers_asgi(app):
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "Client-IP"
    app.config.FORWARDED_FOR_HEADER = "Forwarded"

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.1.1"
    assert response.text == "127.0.1.1"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.text == ""

    headers = {"Client-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.text == "127.0.0.2"


def test_match_info(app):
    @app.route("/api/v1/user/<user_id>/")
    async def handler(request, user_id):
        return json(request.match_info)

    request, response = app.test_client.get("/api/v1/user/sanic_user/")

    assert request.match_info == {"user_id": "sanic_user"}
    assert json_loads(response.text) == {"user_id": "sanic_user"}


@pytest.mark.asyncio
async def test_match_info_asgi(app):
    @app.route("/api/v1/user/<user_id>/")
    async def handler(request, user_id):
        return json(request.match_info)

    request, response = await app.asgi_client.get("/api/v1/user/sanic_user/")

    assert request.match_info == {"user_id": "sanic_user"}
    assert json_loads(response.text) == {"user_id": "sanic_user"}


# ------------------------------------------------------------ #
#  POST
# ------------------------------------------------------------ #


def test_post_json(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}

    request, response = app.test_client.post(
        "/", data=json_dumps(payload), headers=headers
    )

    assert request.json.get("test") == "OK"
    assert request.json.get("test") == "OK"  # for request.parsed_json
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_post_json_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}

    request, response = await app.asgi_client.post(
        "/", data=json_dumps(payload), headers=headers
    )

    assert request.json.get("test") == "OK"
    assert request.json.get("test") == "OK"  # for request.parsed_json
    assert response.text == "OK"


def test_post_form_urlencoded(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == "OK"
    assert request.form.get("test") == "OK"  # For request.parsed_form


@pytest.mark.asyncio
async def test_post_form_urlencoded_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == "OK"
    assert request.form.get("test") == "OK"  # For request.parsed_form


@pytest.mark.parametrize(
    "payload",
    [
        "------sanic\r\n"
        'Content-Disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
        "------sanic\r\n"
        'content-disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
    ],
)
def test_post_form_multipart_form_data(app, payload):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = app.test_client.post(data=payload, headers=headers)

    assert request.form.get("test") == "OK"


@pytest.mark.parametrize(
    "payload",
    [
        "------sanic\r\n"
        'Content-Disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
        "------sanic\r\n"
        'content-disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
    ],
)
@pytest.mark.asyncio
async def test_post_form_multipart_form_data_asgi(app, payload):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == "OK"


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "http://{}:{}/foo"),
        ("/bar/baz", "", "http://{}:{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "http://{}:{}/moo/boo?arg1=val1"),
    ],
)
def test_url_attributes_no_ssl(app, path, query, expected_url):
    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = app.test_client.get(path + "?{}".format(query))
    assert request.url == expected_url.format(HOST, PORT)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "http://{}/foo"),
        ("/bar/baz", "", "http://{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "http://{}/moo/boo?arg1=val1"),
    ],
)
@pytest.mark.asyncio
async def test_url_attributes_no_ssl_asgi(app, path, query, expected_url):
    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = await app.asgi_client.get(path + "?{}".format(query))
    assert request.url == expected_url.format(ASGI_HOST)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "https://{}:{}/foo"),
        ("/bar/baz", "", "https://{}:{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "https://{}:{}/moo/boo?arg1=val1"),
    ],
)
def test_url_attributes_with_ssl_context(app, path, query, expected_url):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(
        os.path.join(current_dir, "certs/selfsigned.cert"),
        keyfile=os.path.join(current_dir, "certs/selfsigned.key"),
    )

    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = app.test_client.get(
        "https://{}:{}".format(HOST, PORT) + path + "?{}".format(query),
        server_kwargs={"ssl": context},
    )
    assert request.url == expected_url.format(HOST, PORT)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "https://{}:{}/foo"),
        ("/bar/baz", "", "https://{}:{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "https://{}:{}/moo/boo?arg1=val1"),
    ],
)
def test_url_attributes_with_ssl_dict(app, path, query, expected_url):

    current_dir = os.path.dirname(os.path.realpath(__file__))
    ssl_cert = os.path.join(current_dir, "certs/selfsigned.cert")
    ssl_key = os.path.join(current_dir, "certs/selfsigned.key")

    ssl_dict = {"cert": ssl_cert, "key": ssl_key}

    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = app.test_client.get(
        "https://{}:{}".format(HOST, PORT) + path + "?{}".format(query),
        server_kwargs={"ssl": ssl_dict},
    )
    assert request.url == expected_url.format(HOST, PORT)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


def test_invalid_ssl_dict(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_dict = {"cert": None, "key": None}

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": ssl_dict}
        )

    assert str(excinfo.value) == "SSLContext or certificate and key required."


def test_form_with_multiple_values(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "selectedItems=v1&selectedItems=v2&selectedItems=v3"

    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.getlist("selectedItems") == ["v1", "v2", "v3"]


@pytest.mark.asyncio
async def test_form_with_multiple_values_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "selectedItems=v1&selectedItems=v2&selectedItems=v3"

    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.getlist("selectedItems") == ["v1", "v2", "v3"]


def test_request_string_representation(app):
    @app.route("/", methods=["GET"])
    async def get(request):
        return text("OK")

    request, _ = app.test_client.get("/")
    assert repr(request) == "<Request: GET />"


@pytest.mark.asyncio
async def test_request_string_representation_asgi(app):
    @app.route("/", methods=["GET"])
    async def get(request):
        return text("OK")

    request, _ = await app.asgi_client.get("/")
    assert repr(request) == "<Request: GET />"


@pytest.mark.parametrize(
    "payload,filename",
    [
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
    ],
)
def test_request_multipart_files(app, payload, filename):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert request.files.get("test").name == filename


@pytest.mark.parametrize(
    "payload,filename",
    [
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
    ],
)
@pytest.mark.asyncio
async def test_request_multipart_files_asgi(app, payload, filename):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert request.files.get("test").name == filename


def test_request_multipart_file_with_json_content_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.json"\r\n'
        "Content-Type: application/json\r\n"
        "Content-Length: 0"
        "\r\n"
        "\r\n"
        "------sanic--"
    )

    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert request.files.get("file").type == "application/json"


@pytest.mark.asyncio
async def test_request_multipart_file_with_json_content_type_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.json"\r\n'
        "Content-Type: application/json\r\n"
        "Content-Length: 0"
        "\r\n"
        "\r\n"
        "------sanic--"
    )

    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert request.files.get("file").type == "application/json"


def test_request_multipart_file_without_field_name(app, caplog):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        '------sanic\r\nContent-Disposition: form-data; filename="test.json"'
        "\r\nContent-Type: application/json\r\n\r\n\r\n------sanic--"
    )

    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = app.test_client.post(
        data=payload, headers=headers, debug=True
    )
    with caplog.at_level(logging.DEBUG):
        request.form

    assert caplog.record_tuples[-1] == (
        "sanic.root",
        logging.DEBUG,
        "Form-data field does not have a 'name' parameter "
        "in the Content-Disposition header",
    )


def test_request_multipart_file_duplicate_filed_name(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json2"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b--\r\n"
    )

    headers = {
        "Content-Type": "multipart/form-data; boundary=e73ffaa8b1b2472b8ec848de833cb05b"
    }

    request, _ = app.test_client.post(
        data=payload, headers=headers, debug=True
    )
    assert request.form.getlist("file") == [
        '{"test":"json"}',
        '{"test":"json2"}',
    ]


@pytest.mark.asyncio
async def test_request_multipart_file_duplicate_filed_name_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json2"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b--\r\n"
    )

    headers = {
        "Content-Type": "multipart/form-data; boundary=e73ffaa8b1b2472b8ec848de833cb05b"
    }

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert request.form.getlist("file") == [
        '{"test":"json"}',
        '{"test":"json2"}',
    ]


def test_request_multipart_with_multiple_files_and_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="test.json"'
        "\r\nContent-Type: application/json\r\n\r\n\r\n"
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="some_file.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n\r\n------sanic--"
    )
    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert len(request.files.getlist("file")) == 2
    assert request.files.getlist("file")[0].type == "application/json"
    assert request.files.getlist("file")[1].type == "application/pdf"


@pytest.mark.asyncio
async def test_request_multipart_with_multiple_files_and_type_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="test.json"'
        "\r\nContent-Type: application/json\r\n\r\n\r\n"
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="some_file.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n\r\n------sanic--"
    )
    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert len(request.files.getlist("file")) == 2
    assert request.files.getlist("file")[0].type == "application/json"
    assert request.files.getlist("file")[1].type == "application/pdf"


def test_request_repr(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/")
    assert repr(request) == "<Request: GET />"

    request.method = None
    assert repr(request) == "<Request: None />"


@pytest.mark.asyncio
async def test_request_repr_asgi(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/")
    assert repr(request) == "<Request: GET />"

    request.method = None
    assert repr(request) == "<Request: None />"


def test_request_bool(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/")
    assert bool(request)

    request.transport = False
    assert not bool(request)


def test_request_parsing_form_failed(app, caplog):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "multipart/form-data"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    with caplog.at_level(logging.ERROR):
        request.form

    assert caplog.record_tuples[-1] == (
        "sanic.error",
        logging.ERROR,
        "Failed when parsing form",
    )


@pytest.mark.asyncio
async def test_request_parsing_form_failed_asgi(app, caplog):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "multipart/form-data"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    with caplog.at_level(logging.ERROR):
        request.form

    assert caplog.record_tuples[-1] == (
        "sanic.error",
        logging.ERROR,
        "Failed when parsing form",
    )


def test_request_args_no_query_string(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/")

    assert request.args == {}


@pytest.mark.asyncio
async def test_request_args_no_query_string_await(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/")

    assert request.args == {}


def test_request_raw_args(app):

    params = {"test": "OK"}

    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/", params=params)

    assert request.raw_args == params


@pytest.mark.asyncio
async def test_request_raw_args_asgi(app):

    params = {"test": "OK"}

    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/", params=params)

    assert request.raw_args == params


def test_request_query_args(app):
    # test multiple params with the same key
    params = [("test", "value1"), ("test", "value2")]

    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/", params=params)

    assert request.query_args == params

    # test cached value
    assert (
        request.parsed_not_grouped_args[(False, False, "utf-8", "replace")]
        == request.query_args
    )

    # test params directly in the url
    request, response = app.test_client.get("/?test=value1&test=value2")

    assert request.query_args == params

    # test unique params
    params = [("test1", "value1"), ("test2", "value2")]

    request, response = app.test_client.get("/", params=params)

    assert request.query_args == params

    # test no params
    request, response = app.test_client.get("/")

    assert not request.query_args


@pytest.mark.asyncio
async def test_request_query_args_asgi(app):
    # test multiple params with the same key
    params = [("test", "value1"), ("test", "value2")]

    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/", params=params)

    assert request.query_args == params

    # test cached value
    assert (
        request.parsed_not_grouped_args[(False, False, "utf-8", "replace")]
        == request.query_args
    )

    # test params directly in the url
    request, response = await app.asgi_client.get("/?test=value1&test=value2")

    assert request.query_args == params

    # test unique params
    params = [("test1", "value1"), ("test2", "value2")]

    request, response = await app.asgi_client.get("/", params=params)

    assert request.query_args == params

    # test no params
    request, response = await app.asgi_client.get("/")

    assert not request.query_args


def test_request_query_args_custom_parsing(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get(
        "/?test1=value1&test2=&test3=value3"
    )

    assert request.get_query_args(keep_blank_values=True) == [
        ("test1", "value1"),
        ("test2", ""),
        ("test3", "value3"),
    ]
    assert request.query_args == [("test1", "value1"), ("test3", "value3")]
    assert request.get_query_args(keep_blank_values=False) == [
        ("test1", "value1"),
        ("test3", "value3"),
    ]

    assert request.get_args(keep_blank_values=True) == RequestParameters(
        {"test1": ["value1"], "test2": [""], "test3": ["value3"]}
    )

    assert request.args == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )

    assert request.get_args(keep_blank_values=False) == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )


@pytest.mark.asyncio
async def test_request_query_args_custom_parsing_asgi(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get(
        "/?test1=value1&test2=&test3=value3"
    )

    assert request.get_query_args(keep_blank_values=True) == [
        ("test1", "value1"),
        ("test2", ""),
        ("test3", "value3"),
    ]
    assert request.query_args == [("test1", "value1"), ("test3", "value3")]
    assert request.get_query_args(keep_blank_values=False) == [
        ("test1", "value1"),
        ("test3", "value3"),
    ]

    assert request.get_args(keep_blank_values=True) == RequestParameters(
        {"test1": ["value1"], "test2": [""], "test3": ["value3"]}
    )

    assert request.args == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )

    assert request.get_args(keep_blank_values=False) == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )


def test_request_cookies(app):

    cookies = {"test": "OK"}

    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/", cookies=cookies)

    assert request.cookies == cookies
    assert request.cookies == cookies  # For request._cookies


@pytest.mark.asyncio
async def test_request_cookies_asgi(app):

    cookies = {"test": "OK"}

    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get("/", cookies=cookies)

    assert request.cookies == cookies
    assert request.cookies == cookies  # For request._cookies


def test_request_cookies_without_cookies(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert request.cookies == {}


@pytest.mark.asyncio
async def test_request_cookies_without_cookies_asgi(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get("/")

    assert request.cookies == {}


def test_request_port(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    port = request.port
    assert isinstance(port, int)

    delattr(request, "_socket")
    delattr(request, "_port")

    port = request.port
    assert isinstance(port, int)
    assert hasattr(request, "_socket")
    assert hasattr(request, "_port")


@pytest.mark.asyncio
async def test_request_port_asgi(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get("/")

    port = request.port
    assert isinstance(port, int)

    delattr(request, "_socket")
    delattr(request, "_port")

    port = request.port
    assert isinstance(port, int)
    assert hasattr(request, "_socket")
    assert hasattr(request, "_port")


def test_request_socket(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    socket = request.socket
    assert isinstance(socket, tuple)

    ip = socket[0]
    port = socket[1]

    assert ip == request.ip
    assert port == request.port

    delattr(request, "_socket")

    socket = request.socket
    assert isinstance(socket, tuple)
    assert hasattr(request, "_socket")


def test_request_form_invalid_content_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    request, response = app.test_client.post("/", json={"test": "OK"})

    assert request.form == {}


@pytest.mark.asyncio
async def test_request_form_invalid_content_type_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    request, response = await app.asgi_client.post("/", json={"test": "OK"})

    assert request.form == {}


def test_endpoint_basic():
    app = Sanic()

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert request.endpoint == "test_requests.my_unique_handler"


@pytest.mark.asyncio
async def test_endpoint_basic_asgi():
    app = Sanic()

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert request.endpoint == "test_requests.my_unique_handler"


def test_endpoint_named_app():
    app = Sanic("named")

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert request.endpoint == "named.my_unique_handler"


@pytest.mark.asyncio
async def test_endpoint_named_app_asgi():
    app = Sanic("named")

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert request.endpoint == "named.my_unique_handler"


def test_endpoint_blueprint():
    bp = Blueprint("my_blueprint", url_prefix="/bp")

    @bp.route("/")
    async def bp_root(request):
        return text("Hello")

    app = Sanic("named")
    app.blueprint(bp)

    request, response = app.test_client.get("/bp")

    assert request.endpoint == "named.my_blueprint.bp_root"


@pytest.mark.asyncio
async def test_endpoint_blueprint_asgi():
    bp = Blueprint("my_blueprint", url_prefix="/bp")

    @bp.route("/")
    async def bp_root(request):
        return text("Hello")

    app = Sanic("named")
    app.blueprint(bp)

    request, response = await app.asgi_client.get("/bp")

    assert request.endpoint == "named.my_blueprint.bp_root"
