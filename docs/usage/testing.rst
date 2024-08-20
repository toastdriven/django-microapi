Testing
=======

``microapi`` includes testing support as part of the package.

Historically, this is one of the pain points of plain old API views in Django.
The built-in test client (rightly) assumes you'll be making form posts and
rendering HTML, so supporting JSON & making/checking payloads is tedious &
repetitive.

The testing support in `django-microapi` tries to address this. Let's start by
looking at an example endpoint, and how we'd write tests for it.

.. note:: If you'd prefer to look at full working code, ``microapi`` dogfoods
    its own testing tools. You can find them within the repository on
    `GitHub <https://github.com/toastdriven/django-microapi/blob/main/test/test_microapi/tests/test_views.py>`_.


Example Endpoint
-----------------

We'll start with the similar code from the :doc:`Tutorial <tutorial>`::

    # blog/api.py
    from microapi import (
        ApiView,
        http,
    )

    from .models import BlogPost


    def serialize_author(serializer, author):
        return {
            "id": author.id,
            "username": author.username,
            "email": author.email,
            "first_name": author.first_name,
            "last_name": author.last_name,
        }


    def serialize_post(serializer, post):
        data = serializer.to_dict(post)
        data["author"] = serialize_author(serializer, post.author)
        return data


    class BlogPostListView(ApiView):
        def serialize(self, obj):
            return serialize_post(obj)

        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })

        def post(self, request):
            if not request.user.is_authenticated:
                return self.render_error("You must be logged in")

            data = self.read_json(request)

            # TODO: Validate the data here.

            post = self.serializer.from_dict(BlogPost(), data)
            post.author = request.user
            post.save()

            return self.render({
                "success": True,
                "post": self.serialize(post),
            }, status_code=http.CREATED)


    class BlogPostDetailView(ApiView):
        def serialize(self, obj):
            return serialize_post(obj)

        def get(self, request, pk):
            try:
                post = BlogPost.objects.get(pk=pk)
            except BlogPost.DoesNotExist:
                return self.render_error("Blog post not found")

            return self.render({
                "success": True,
                "post": self.serialize(post),
            })

        def put(self, request, pk):
            if not request.user.is_authenticated:
                return self.render_error("You must be logged in")

            data = self.read_json(request)

            try:
                post = BlogPost.objects.get(pk=pk)
            except BlogPost.DoesNotExist:
                return self.render_error("Blog post not found")

            post = self.serializer.from_dict(post, data)
            post.save()

            return self.render({
                "success": True,
                "post": self.serialize(post),
            }, status_code=http.ACCEPTED)

        def delete(self, request, pk):
            if not request.user.is_authenticated:
                return self.render_error("You must be logged in")

            try:
                post = BlogPost.objects.get(pk=pk)
            except BlogPost.DoesNotExist:
                return self.render_error("Blog post not found")

            post.delete()

            return self.render({
                "success": True,
            }, status_code=http.NO_CONTENT)


Adding Tests
------------

As with most things, ``microapi`` doesn't dictate where you place your tests,
but following Django's conventions is a good place to start. So we'll assume
that you've made a ``blog/tests`` directory, so that you can have multiple test
files within for various purposes.

We'll create a new file within that directory, ``blog/tests/test_api.py``, to
match our ``blog/api.py`` layout. Within that file, we'll start with the
following code::

    # blog/tests/test_api.py
    from microapi.tests import ApiTestCase

    from ..models import BlogPost


    class BlogPostListViewTestCase(ApiTestCase):
        def test_should_fail(self):
            self.fail("Ensure our tests are being run.")

We're starting with a simple test class, with a single test that should fail
regardless. This will help us ensure our tests are being picked up by the test
runner & failing correctly.

``microapi.tests.ApiTestCase`` is a thin wrapper over the top of Django's own
``TestCase``, with additional methods to support making/receiving API requests
and custom methods to assert things about the payloads or the response codes.

Go run your tests as usual::

    $ ./manage.py test

You should get a failure (as expected)::

    AssertionError: Ensure our tests are being run.

    ----------------------------------------------------------------------
    Ran 1 tests in 0.033s

    FAILED (failures=1)

.. warning:: If you didn't get the expected failure here, something is wrong
    with your setup. Before writing any further tests or putting any further
    time into this guide, you should take the time to fix things so that your
    tests get picked up.

    Common problems/reasons include:

    * mis-named files/directories
    * an app not being included in ``INSTALLED_APPS``
    * mis-naming the ``TestCase`` class within the tests

Now that we're sure our tests are running, let's fix that test case & make sure
the list endpoint is responding to a ``GET`` correctly::

    # blog/tests/test_api.py
    from microapi.tests import ApiTestCase

    from ..models import BlogPost
    # We're importing our view here!
    from ..api import BlogPostListView


    class BlogPostListViewTestCase(ApiTestCase):
        # We're renaming this method!
        def test_get_success(self):
            # Make a test request.
            req = self.create_request(
                "/api/v1/posts/",
            )
            # Make an API request against our view (newly-imported above).
            resp = self.make_request(BlogPostListView, req)
            # Ensure that we got an HTTP 200 OK from the endpoint.
            self.assertOK(resp)

Nothing here is too crazy, though you'll note that we're not directly using
either of Django's included ``django.test.Client``, nor the
``django.test.RequestFactory``. ``Client``, while a great tool normally,
unfortunately makes a bunch of assumptions that are invalid for ``microapi``.

Using ``RequestFactory`` directly is possible, but making API-related requests
with it is kinda painful/repetitive, so we can do better. Enter
``ApiTestCase.create_request``, which uses ``RequestFactory`` under-the-hood.

And in the same vein of trying to eliminate painful/repetitive code,
``ApiTestCase.make_request`` automates the request/response process against a
given ``APIView``. It handles all the instantiation of the view, as well as
performing the request against it, returning a ``HttpResponse`` in the process
as normal.

Finally, because HTTP status codes are more diverse & more important in an
API use case, ``ApiTestCase`` ships with a host of
:doc:`assertion methods <../api/tests>` that check
for common RESTful status codes. In this case, we're just looking for a
``HTTP 200 OK`` from the endpoint, so ``self.assertOK(resp)`` handles that check
for us.

Run your tests::

    $ ./manage.py test

And you should get::

    ----------------------------------------------------------------------
    Ran 1 tests in 0.047s

    OK

🎉 Huzzah! Our code is running, our API is being hit, and our test is passing!

...But before we get too far ahead of ourselves, we should note that what's
coming back from that endpoint right now is just an empty response: there's no
data in our test database!


Inspecting Responses
--------------------

So that we can do more interesting things in this guide, we'll add in the
creation of some basic test data in the database::

    # ...

    class BlogPostListViewTestCase(ApiTestCase):
        # Adding this above the test methods.
        def setUp(self):
            super().setUp()
            self.user = User.objects.create_user(
                "testmctest",
                "teest@mctest.com",
                "testpass",
            )
            self.post_1 = BlogPost.objects.create(
                title="Hello, World!",
                content="My first post! *SURELY*, it won't be the last...",
                published_by=self.user,
                published_on=make_aware(
                    datetime.datetime(2023, 11, 28, 9, 26, 54, 123456),
                    timezone=datetime.timezone.utc,
                ),
            )
            self.post_2 = BlogPost.objects.create(
                title="Life Update",
                content="So, it's been awhile...",
                published_by=self.user,
                published_on=make_aware(
                    datetime.datetime(2023, 12, 5, 10, 3, 22, 123456),
                    timezone=datetime.timezone.utc,
                ),
            )

Running the tests should get us the same result, since we don't have any methods
asserting anything about the API response(s)::

    ----------------------------------------------------------------------
    Ran 1 tests in 0.047s

    OK

However, we should now have actual data coming back as part of the list
endpoint. So let's inspect that data & make some assertions about it::

    # blog/tests/test_api.py
    # We're changing up the import here & adding in `check_response`!
    from microapi.tests import (
        ApiTestCase,
        check_response,
    )

    # ...

    class BlogPostListViewTestCase(ApiTestCase):
        # ...

        def test_get_success(self):
            req = self.create_request(
                "/api/v1/posts/",
            )
            resp = self.make_request(BlogPostListView, req)
            self.assertOK(resp)

            # New code here!
            data = check_response(resp)
            # Here, we're just using the built-in `assert*` methods to inspect
            # the response data, just like asserting about any other `dict`.
            self.assertTrue(data["success"])
            self.assertEqual(len(data["posts"]), 2)
            # Note that, because we're creating a stable ordering via
            # `.order_by("-created")`, we can count on these being in this
            # order.
            # If you have an unstable sort order, you'll need to do extra work
            # to make sure tests like these will consistently pass.
            self.assertEqual(data["posts"][0]["title"], "Life Update")
            self.assertEqual(data["posts"][1]["title"], "Hello, World!")

The (unassuming) star of the show here is the newly-added ``check_response``.
It's a utility method that takes a given ``HttpResponse``, checks for
appropriate JSON headers, and will automatically decode & return the response
body for you.

After processing the response with ``check_response``, the data you get back is
a Python representation of the JSON payload (or an empty ``dict`` if there was
no payload).


Testing Data-Creating Endpoints
-------------------------------

Another pain-point of testing APIs is testing endpoints/methods that should
create data. Forming a proper request, with the right
method/headers/encoded-payload/etc., is tedious.

But, using the tools we've already introduced, this gets much easier.
So now we'll add on another test method to exercise the ``POST`` & create a blog
post with it.

We'll start by adding the new method to the same test case::

    class BlogPostListViewTestCase(ApiTestCase):
        # ...

        def test_post_success(self):
            # While not required, I like to include a sanity-check at the
            # beginning of a test method, to ensure the DB is in the expected
            # state.
            # We should only have the two blog posts that are created in the
            # `setUp` method present.
            self.assertEqual(BlogPost.objects.all().count(), 2)

            # We'll take advantage of some of the optional arguments to
            # `create_request`...
            req = self.create_request(
                "/api/v1/posts/",
                method="post",
                data={
                    "title": "Cat Pictures",
                    "content": "All the internet is good for.",
                    "published_on": "2023-12-05T11:45:45.000000-0600",
                },
                user=self.user,
            )
            # Then make the request & check the response in a similar fashion
            # to the last test method.
            resp = self.make_request(BlogPostListView, req)
            # Since we expect a different status code, we use `assertCreated`
            # here in place of `assertOK`.
            self.assertCreated(resp)

            # Finally, a simple assertion about the state of the DB.
            # We should ensure the new post is present.
            self.assertEqual(BlogPost.objects.all().count(), 3)

The only substantially different code here is how we create the request via
``ApiTestCase.create_request``. We can provide the HTTP method to use, and the
data to be automatically JSON-encoded for us.

Now when we run our tests, we should get back something like::

    ----------------------------------------------------------------------
    Ran 2 tests in 0.053s

    OK

And we know our API is behaving properly.


"Final" API Test Code
---------------------

Putting everything together, our completed test code should look like::

    # blog/tests/test_api.py
    from microapi.tests import (
        ApiTestCase,
        check_response,
    )

    from ..models import BlogPost
    from ..api import BlogPostListView

    class BlogPostListViewTestCase(ApiTestCase):
        def setUp(self):
            super().setUp()
            self.user = User.objects.create_user(
                "testmctest",
                "teest@mctest.com",
                "testpass",
            )
            self.post_1 = BlogPost.objects.create(
                title="Hello, World!",
                content="My first post! *SURELY*, it won't be the last...",
                published_by=self.user,
                published_on=make_aware(
                    datetime.datetime(2023, 11, 28, 9, 26, 54, 123456),
                    timezone=datetime.timezone.utc,
                ),
            )
            self.post_2 = BlogPost.objects.create(
                title="Life Update",
                content="So, it's been awhile...",
                published_by=self.user,
                published_on=make_aware(
                    datetime.datetime(2023, 12, 5, 10, 3, 22, 123456),
                    timezone=datetime.timezone.utc,
                ),
            )

        def test_get_success(self):
            req = self.create_request(
                "/api/v1/posts/",
            )
            resp = self.make_request(BlogPostListView, req)
            self.assertOK(resp)

            data = check_response(resp)
            self.assertTrue(data["success"])
            self.assertEqual(len(data["posts"]), 2)
            self.assertEqual(data["posts"][0]["title"], "Life Update")
            self.assertEqual(data["posts"][1]["title"], "Hello, World!")

        def test_post_success(self):
            # Sanity-check.
            self.assertEqual(BlogPost.objects.all().count(), 2)

            req = self.create_request(
                "/api/v1/posts/",
                method="post",
                data={
                    "title": "Cat Pictures",
                    "content": "All the internet is good for.",
                    "published_on": "2023-12-05T11:45:45.000000-0600",
                },
                user=self.user,
            )
            resp = self.make_request(BlogPostListView, req)
            self.assertCreated(resp)

            self.assertEqual(BlogPost.objects.all().count(), 3)


Pytest Support
--------------

`pytest <https://pytest.org/>`_ is a fairly common/popular testing package
within the Python community, and ``microapi`` ships with first-class support for
it.

``microapi.test`` includes a host of utility functions that can be directly used
within your ``pytest`` test methods to exercise API endpoints. The full list
is available in the :doc:`../api/tests` reference.

In fact, everything that we covered above as part of ``ApiTestCase`` *actually*
uses the **function-based** utilities/assertions built for ``pytest``, neatly
wrapped in a more familiar class-based approach.

So we could re-write our ``blog/tests/test_api.py`` like so for ``pytest``::

    # blog/tests/test_api.py
    # Note that our imports here are quite different!
    from microapi.tests import (
        assert_created,
        assert_ok,
        create_request,
        check_response,
    )

    from ..models import BlogPost
    from ..api import BlogPostListView

    def setup_posts():
        # There are better ways to do fixtures, but for the sake of keeping
        # things familiar to the above code...
        user = User.objects.create_user(
            "testmctest",
            "teest@mctest.com",
            "testpass",
        )
        post_1 = BlogPost.objects.create(
            title="Hello, World!",
            content="My first post! *SURELY*, it won't be the last...",
            published_by=user,
            published_on=make_aware(
                datetime.datetime(2023, 11, 28, 9, 26, 54, 123456),
                timezone=datetime.timezone.utc,
            ),
        )
        post_2 = BlogPost.objects.create(
            title="Life Update",
            content="So, it's been awhile...",
            published_by=user,
            published_on=make_aware(
                datetime.datetime(2023, 12, 5, 10, 3, 22, 123456),
                timezone=datetime.timezone.utc,
            ),
        )

    def test_posts_get_success(self):
        setup_posts()

        req = create_request(
            "/api/v1/posts/",
        )
        view_func = BlogPostListView.as_view()
        # Don't forget to supply args/kwargs as they'd be received from the
        # URLconf here!
        resp = view_func(req)
        assert_ok(resp)

        data = check_response(resp)
        assert data["success"] == True
        assert len(data["posts"] == 2
        assert data["posts"][0]["title"] == "Life Update"
        assert data["posts"][1]["title"] == "Hello, World!"

    def test_post_success(self):
        setup_posts()

        # Sanity-check.
        assert BlogPost.objects.all().count() == 2

        req = create_request(
            "/api/v1/posts/",
            method="post",
            data={
                "title": "Cat Pictures",
                "content": "All the internet is good for.",
                "published_on": "2023-12-05T11:45:45.000000-0600",
            },
            user=user,
        )
        view_func = BlogPostListView.as_view()
        # Don't forget to supply args/kwargs as they'd be received from the
        # URLconf here!
        resp = view_func(req)
        assert_created(resp)

        assert BlogPost.objects.all().count() == 3

And running them with ``pytest`` should yield something like::

    collected 2 items

    blog/tests/test_api.py ..                  [100%]

    =============== 2 passed in 0.21s ===============
