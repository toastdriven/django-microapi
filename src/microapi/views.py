import json

from django.http import JsonResponse
from django.views.generic.base import View

from .exceptions import (
    ApiError,
    # InvalidFieldError,
    # DataValidationError,
)
from . import http
from .serializers import ModelSerializer


class ApiView(View):
    """
    Just a bit of sugar on top of plain ol' `View`.

    Used as a base class for your API views to inherit from, & provides
    conveniences to make writing JSON APIs easier.

    Usage::

        from django.contrib.auth.decorators import login_required

        from microapi import ApiView, ModelSerializer

        from .models import BlogPost


        # Inherit from the `ApiView` class...
        class BlogPostView(ApiView):
            # ...then define `get`/`post`/`put`/`delete`/`patch` methods on the
            # subclass.

            # For example, we'll provide a list view on `get`.
            def get(self, request):
                posts = BlogPost.objects.all().order_by("-created")

                # The `render` method automatically creates a JSON response from
                # the provided data.
                return self.render({
                    "success": True,
                    "posts": self.serialize_many(posts),
                })

            # And handle creating a new blog post on `post`.
            @login_required
            def post(self, request):
                # Read the JSON
                data = self.read_json(request)

                # TODO: Validate the data here.

                serializer = ModelSerializer()
                post = serializer.from_dict(BlogPost(), data)
                post.save()

                return self.render({
                    "success": True,
                    "post": self.serialize(post),
                })

    """

    bubble_exceptions = False
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
    ]

    def dispatch(self, request, *args, **kwargs):
        """
        Light override to the built-in `dispatch`, to allow for automatic
        JSON serialization of errors (as opposed to HTML).

        If you need the Django debug error, you can set the `bubble_exceptions`
        attribute on the class to `True`.

        Args:
            request (HttpRequest): The provided request.
            *args (list): The unnamed view arguments from the URLconf.
            **kwargs (dict): The named view arguments from the URLconf.

        Returns:
            HttpResponse: Typically, a JSON-encoded response.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as err:
            if self.bubble_exceptions:
                raise

            return self.render_error(str(err))

    def read_json(self, request, strict=True):
        """
        Reads the request body & returns the decoded JSON.

        Args:
            request (HttpRequest): The received request
            strict (bool): (Optional) If provided, requires "correct" JSON
                headers to be present. Default is `True`.

        Returns:
            dict: The decoded JSON body
        """
        valid_content_types = [
            "application/json",
        ]

        if strict:
            # Check the Content-Type.
            if request.headers.get("Content-type", "") not in valid_content_types:
                raise ApiError("Invalid Content-type provided.")

        try:
            return json.loads(request.body.read())
        except ValueError:
            raise ApiError("Invalid JSON payload provided.")

    def render(self, data, status_code=http.OK):
        """
        Creates a JSON response.

        Args:
            data (dict): The data to return as JSON
            status_code (int): The desired HTTP status code. Default is
                `http.OK` (a.k.a. `200`).

        Returns:
            JsonResponse: The response for Django to provide to the user
        """
        return JsonResponse(data, status=status_code)

    def render_error(self, msgs, status_code=http.APP_ERROR):
        """
        Creates an error JSON response.

        Args:
            msgs (list|str): A list of message(s) to provide to the user. If a
                single string is provided, this will automatically get turned
                into a list.
            status_code (int): The desired HTTP status code. Default is
                `http.APP_ERROR` (a.k.a. `500`).

        Returns:
            JsonResponse: The error response for Django to provide to the user
        """
        if not isinstance(msgs, (list, tuple)):
            # In case of a single string.
            msgs = [msgs]

        return self.render(
            {
                "success": False,
                "errors": msgs,
            },
            status_code=status_code,
        )

    def validate(self, data):
        """
        A method for standardizing validation. Not automatically called
        anywhere.

        Expected behavior is to return the validated data on success, or to
        call `render_error` with failures.

        This **MUST** be implemented in the subclass by the user.

        Args:
            data (dict): The data provided by the user.

        Returns:
            dict: The validated data
        """
        raise NotImplementedError("Subclass must implement the 'validate' method.")

    def serialize(self, obj):
        """
        A method for standardizing serialization.

        A "rich" object (like a `Model`) is provided, & turned into a dict that
        is ready for JSON serialization.

        By default, this provides some basic serialization for Django `Model`
        instances via `ModelSerializer`. You can extend this method to embelish
        the data, or override to perform your own custom serialization.

        Args:
            obj (Model): The object to serialize.

        Returns:
            dict: The data
        """
        serializer = ModelSerializer()
        return serializer.to_dict(obj)

    def serialize_many(self, objs):
        """
        Like `serialize`, but handles serialization for many objects.

        Args:
            objs (iterable): An iterable of the objects to serialize.

        Returns:
            list: A list of serialized objects
        """
        data = []

        for obj in objs:
            data.append(self.serialize(obj))

        return data
