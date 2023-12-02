import json

from django.test import (
    RequestFactory,
    TestCase,
)

from . import http


# Some assert methods, useful for `pytest` or similar.
def assert_status_code(resp, status_code):
    """
    Checks the response for a specific status code.

    There are many specialized variants included with this library, so this
    is really only needed when you need to support a rarer HTTP status code.

    Args:
        resp (django.http.HttpResponse): The response from the view.
        status_code (int): The desired HTTP status code.

    Raises:
        AssertionError: If the expected status code does not match the response.
    """
    assert resp.status_code == status_code


def assert_ok(resp):
    """
    Checks the response for an `HTTP 200 OK`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `200`.
    """
    assert_status_code(resp, status_code=http.OK)


def assert_created(resp):
    """
    Checks the response for an `HTTP 201 Created`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `201`.
    """
    assert_status_code(resp, status_code=http.CREATED)


def assert_accepted(resp):
    """
    Checks the response for an `HTTP 202 Accepted`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `202`.
    """
    assert_status_code(resp, status_code=http.ACCEPTED)


def assert_no_content(resp):
    """
    Checks the response for an `HTTP 204 No Content`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `204`.
    """
    assert_status_code(resp, status_code=http.NO_CONTENT)


def assert_bad_request(resp):
    """
    Checks the response for an `HTTP 400 Bad Request`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `400`.
    """
    assert_status_code(resp, status_code=http.BAD_REQUEST)


def assert_unauthorized(resp):
    """
    Checks the response for an `HTTP 401 Unauthorized`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `401`.
    """
    assert_status_code(resp, status_code=http.UNAUTHORIZED)


def assert_forbidden(resp):
    """
    Checks the response for an `HTTP 403 Forbidden`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `403`.
    """
    assert_status_code(resp, status_code=http.FORBIDDEN)


def assert_not_found(resp):
    """
    Checks the response for an `HTTP 404 Not Found`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `404`.
    """
    assert_status_code(resp, status_code=http.NOT_FOUND)


def assert_not_allowed(resp):
    """
    Checks the response for an `HTTP 405 Not Allowed`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `405`.
    """
    assert_status_code(resp, status_code=http.NOT_ALLOWED)


def assert_app_error(resp):
    """
    Checks the response for an `HTTP 500 Application Error`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Raises:
        AssertionError: If the response's status code is not a `500`.
    """
    assert_status_code(resp, status_code=http.APP_ERROR)


def check_response(resp):
    """
    Checks for a valid response & returns the decoded JSON data.

    This checks for:
    * A valid `Content-Type` header
    * Loads the JSON body

    If no body is present, this returns an empty `dict`.

    Args:
        resp (django.http.HttpResponse): The response from the view.

    Returns:
        dict: The loaded data, if any.

    Raises:
        AssertionError: If the `Content-Type` header doesn't contain the JSON
            header.
        ValueError: If a body is present, but is not valid JSON.
    """
    assert "application/json" in resp.headers.get("Content-Type", "")

    body_data = resp.body.read()

    if len(body_data):
        return json.loads(body_data)

    return {}


def create_request(url, method="GET", headers=None, data=None, factory=None):
    """
    Creates a `Request` object (via a `django.test.RequestFactory`).

    Args:
        url (str): The URL as entered by the user.
        method (str): The HTTP method used. Case-insensitive. Default is `GET`.
        headers (dict): The HTTP headers on the request. Default is `None`,
            which turns into basic JSON headers.
        data (dict): The JSON data to send. Default is `None`.
        factory (RequestFactory): (Optional) Allows for providing a different
            `RequestFactory`. Default is `django.test.RequestFactory`.

    Returns:
        Request: The built request object.
    """
    if headers is None:
        headers = {
            "Content-Type": "application/json",
            "Accepts": "application/json",
        }

    if factory is None:
        factory = RequestFactory()

    if method.lower() == "get":
        req_method = factory.get
    elif method.lower() == "post":
        req_method = factory.post
    elif method.lower() == "put":
        req_method = factory.put
    elif method.lower() == "delete":
        req_method = factory.delete
    elif method.lower() == "patch":
        raise ValueError("Django's RequestFactory does not support PATCH.")
    elif method.lower() == "head":
        req_method = factory.head
    elif method.lower() == "options":
        req_method = factory.options
    elif method.lower() == "trace":
        req_method = factory.trace

    return req_method(
        url,
        data=data,
        headers=headers,
    )


class ApiTestCase(TestCase):
    """
    A lightly customized `TestCase` that provide convenience methods for
    making API requests & checking API responses.

    This does not do anything automatically (beyond creating a `self.factory`
    for making requests).
    """

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def make_request(self, view_class, url, method="GET", headers=None, data=None):
        """
        Creates a `Request` object and simulates the request/response cycle
        against a given `View` class.

        Args:
            view_class (View): The view class that should be tested.
            url (str): The URL as entered by the user.
            method (str): The HTTP method used. Case-insensitive.
                Default is `GET`.
            headers (dict): The HTTP headers on the request. Default is `None`,
                which turns into basic JSON headers.
            data (dict): The JSON data to send. Default is `None`.
            factory (RequestFactory): (Optional) Allows for providing a
                different `RequestFactory`.
                Default is `django.test.RequestFactory`.

        Returns:
            Response: The received response object from calling the view.
        """
        req = self.create_request(url, method=method, headers=headers, data=data)
        view = view_class.as_view()
        return view(req)

    def assertStatusCode(self, resp, status_code):
        """
        Checks the response for a specific status code.

        There are many specialized variants included with this class, so this
        is really only needed when you need to support a rarer HTTP status code.

        Args:
            resp (django.http.HttpResponse): The response from the view.
            status_code (int): The desired HTTP status code.

        Raises:
            AssertionError: If the expected status code does not match the
                response.
        """
        assert_status_code(resp, status_code)

    def assertOK(self, resp):
        """
        Checks the response for an `HTTP 200 OK`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `200`.
        """
        assert_ok(resp)

    def assertCreated(self, resp):
        """
        Checks the response for an `HTTP 201 Created`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `201`.
        """
        assert_created(resp)

    def assertAccepted(self, resp):
        """
        Checks the response for an `HTTP 202 Accepted`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `202`.
        """
        assert_accepted(resp)

    def assertNoContent(self, resp):
        """
        Checks the response for an `HTTP 204 No Content`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `204`.
        """
        assert_no_content(resp)

    def assertBadRequest(self, resp):
        """
        Checks the response for an `HTTP 400 Bad Request`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `400`.
        """
        assert_bad_request(resp)

    def assertUnauthorized(self, resp):
        """
        Checks the response for an `HTTP 401 Unauthorized`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `401`.
        """
        assert_unauthorized(resp)

    def assertForbidden(self, resp):
        """
        Checks the response for an `HTTP 403 Forbidden`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `403`.
        """
        assert_forbidden(resp)

    def assertNotFound(self, resp):
        """
        Checks the response for an `HTTP 404 Not Found`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `404`.
        """
        assert_not_found(resp)

    def assertNotAllowed(self, resp):
        """
        Checks the response for an `HTTP 405 Not Allowed`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `405`.
        """
        assert_not_allowed(resp)

    def assertAppError(self, resp):
        """
        Checks the response for an `HTTP 500 Application Error`.

        Args:
            resp (django.http.HttpResponse): The response from the view.

        Raises:
            AssertionError: If the response's status code is not a `500`.
        """
        assert_app_error(resp)

    def assertResponseEquals(self, resp, data):
        """
        Checks for a valid response & asserts the response body matches the
        expected data.

        This checks for:
        * A valid `Content-Type` header
        * Loads the JSON body
        * Asserts the response data equals the expected data

        Args:
            resp (django.http.HttpResponse): The response from the view.
            data (dict or list): The expected data.

        Raises:
            AssertionError: If the response is invalid or doesn't match the data.
            ValueError: If a body is present, but is not valid JSON.
        """
        resp_data = check_response(resp)
        assert data == data
