Tutorial
========

A tiny library to make writing CBV-based APIs easier in Django.

Essentially, this just provides some sugar on top of the plain old
``django.views.generic.base.View`` class, all with the intent of making handling
JSON APIs easier (without the need for a full framework).

Let's walk through adding it to an existing blogging application.


Setup
-----

``django-microapi`` is easy to add to an existing project. Its only dependency
is `Django <https://djangoproject.com/>`_ itself, with pretty much any modern
release being supported.

Installation is easy::

    $ pip install django-microapi

It doesn't need to be added to ``INSTALLED_APPS``, and you can just import
``microapi`` wherever you need it.

.. note:: When importing, it's just ``microapi``, even though the package
    name is ``django-microapi``. This is done to prevent cluttering up the
    `PyPI <https://pypi.org/>`_ namespace & make it clear what the package
    works with.


The Existing Application
------------------------

We'll assume you've implemented a relatively straight-forward blogging
application. For brevity, we'll assume the ``models.py`` within the application
looks something like::

    # blog/models.py
    from django.contrib.auth import get_user_model
    from django.db import models
    from django.utils.text import slugify


    # Because who knows? Maybe you have a custom model...
    User = get_user_model()


    class BlogPost(models.Model):
        title = models.CharField(max_length=128)
        slug = models.SlugField(blank=True, db_index=True)
        author = models.ForeignKey(
            User,
            related_name="blog_posts",
            on_delete=models.CASCADE,
        )
        content = models.TextField(blank=True, default="")
        created = models.DateTimeField(
            auto_now_add=True,
            blank=True,
            db_index=True,
        )
        updated = models.DateTimeField(
            auto_now=True,
            blank=True,
            db_index=True,
        )

        def __str__(self):
            return f"{self.title}"

        def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = slugify(self.title)

            return super().save(*args, **kwargs)


Your First Steps
----------------

We'll get started integrating by creating a simple list endpoint that responds
to an HTTP GET.

Where you put this code is up to you, as long as it's importable into your
URLconf (e.g. ``blog/urls.py``). It's fine to place it in ``views.py`` if your
application already has HTML-based views.

Alternatively, I like to put them in a separate ``api.py`` file within the app
(e.g. ``blog/api.py``), so that I'm not mixing the API & HTML code in the same
file. Regardless, there's no *"wrong"* way to do it.

For now, let's assume there's already stuff in ``blog/views.py``, so we'll create
an empty ``blog/api.py`` file.

Then we'll start with the following code::

    # blog/api.py
    from microapi import ApiView

    from .models import BlogPost


    class BlogPostListView(ApiView):
        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })

Let's step through what we've added to the file.

First, we want to import the ``ApiView`` class from ``microapi``. This class
builds on Django's own ``django.views.generic.base.View`` class-based view, but
provides a couple additional useful bits for our use.

We then create a new class, ``BlogPostListView``, and inherit from the
``ApiView`` class we imported. Like any other ``View`` subclass, we can define
methods on it to handle specific HTTP verbs (e.g.
``get``, ``post``, ``put``, ``delete``, etc.).

Because most RESTful APIs return a list when sending a ``GET`` to the top-level
endpoint, we implement our logic in the ``BlogPostListView.get`` method::

    class BlogPostListView(ApiView):
        # ...

        # We get the `HttpRequest` just like normal.
        # Optionally, we also accept any URLconf parameters (none in this
        # example).
        def get(self, request):
            # We collect a list of all the blog posts from the database via the
            # ORM, just like normal.
            posts = BlogPost.objects.all().order_by("-created")

            # Then we create a JSON response of all of them.
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })

The most interesting part is the call to ``self.render(...)``. Similar to
Django's ``django.shortcuts.render``, this takes some data & creates a
``HttpResponse`` to serve back to the user.

However, in this case, rather than rendering a template & generating HTML, this
converts the data into an equivalent *JSON response*. We'll see what the result
looks like after we finish hooking up the endpoint, which we'll do next.


Hook Up the API Endpoint
------------------------

We've build the API endpoint, but we haven't hooked it up to a URL yet.
So we'll go to our URLconf (``blog/urls.py``), and hook it in a familiar way::

    # blog/urls.py
    from django.urls import path

    # Just import the new API class...
    from .api import BlogPostListView

    urlpatterns = [
        # ...then hook it up like any other CBV.
        path("api/v1/posts/", BlogPostListView.as_view()),
    ]

Now, assuming that's included in the main URLconf (e.g.
``path("", include("blog.urls")),``), the user can hit the endpoint in a
browser & get a list of the blog posts!

For example, visiting http://localhost:8000/api/v1/posts/ might yield something
like::

    {
        "success": True,
        "posts": [
            {
                "id": 2,
                "title": "Status Update",
                "slug": "status-update",
                "content": "I just wanted to drop a quick update.",
                "created": "2024-01-11-T11:35:12.000-0600",
                "updated": "2024-01-11-T11:35:12.000-0600",
            },
            {
                "id": 1,
                "title": "Hello, world!",
                "slug": "hello-world",
                "content": "My first post to my blog!",
                "created": "2024-01-09-T20:10:55.000-0600",
                "updated": "2024-01-09-T20:10:55.000-0600",
            }
        ]
    }

Yay! With a relatively minimal amount of code, our first bit of API works!

.. note:: You may have noticed that something (``author``) is missing from
    the JSON output. This is actually intentional, as ``microapi``'s take on
    serialization is a very simplistic one. We'll talk more about serialization
    next as part of the detail endpoint.


Adding a Detail Endpoint
------------------------

Now that we can accept ``HTTP GET`` requests for a list endpoint, a common
follow-up request is a ``HTTP GET`` **detail** endpoint. Let's add that now.

As opposed to many API frameworks, ``microapi.ApiView`` is very
endpoint/URL-focused. As a result of this, because the detail endpoint (e.g.
``/api/v1/posts/<int:pk>/``) is separate/distinct from the list endpoint (e.g.
``/api/v1/posts/``), we'll need a *separate/distinct* API view to handle it.

So, back within ``api.py``, we'll add a second class::

    # blog/api.py
    from microapi import ApiView

    from .models import BlogPost


    # What we previously defined.
    class BlogPostListView(ApiView):
        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })


    # Here's where the new code is!
    # Note that while similar, this is a different name from above.
    class BlogPostDetailView(ApiView):
        # ...and this method signature is different!
        def get(self, request, pk):
            try:
                post = BlogPost.objects.get(pk=pk)
            except BlogPost.DoesNotExist:
                return self.render_error("Blog post not found")

            return self.render({
                "success": True,
                "post": self.serialize(post),
            })

Before we forget, let's hook up the new endpoint, then we'll talk about how this
new endpoint is different::

    # blog/urls.py
    from django.urls import path

    # Import both classes.
    from .api import (
        BlogPostListView,
        BlogPostDetailView,
    )

    urlpatterns = [
        # The previously added list endpoint...
        path("api/v1/posts/", BlogPostListView.as_view()),
        # ...and the new detail endpoint!
        path("api/v1/posts/<int:pk>/", BlogPostDetailView.as_view()),
    ]

While this new code is very similar to the list endpoint, there are a couple
key differences to talk about:

* Different ``get(...)`` signature
* Catching a failed lookup & returning an error with ``render_error``
* The use of ``serialize(...)`` instead of ``serialize_many(...)``

Different ``get(...)`` Signature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The different method signature on ``BlogPostDetailView.get(...)`` comes down to
the addition of a new parameter, ``pk``.

Like a normal Django function-based (or class-based) view, we can accept
additional parameters *from the URLconf*. In this case, the URLconf captures the
blog post's primary key as ``pk``, which then gets passed along for use to the
view method.

.. note:: ``microapi`` doesn't enforce any constraints on captures, so
    you can capture/use as many parameters as you want from a URLconf.
    This can be great for things like nested endpoints, or supporting more
    complicated URLs.

Catching a Failed Lookup & Returning an Error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's turn our attention to the lookup/fetch of the post::

    try:
        post = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        return self.render_error("Blog post not found")

One of the niceties built into ``microapi`` is the ability to handle/return
errors in an API-friendly way.

Normally when Django encounters an error, depending on the value of
``settings.DEBUG``, it'll either return an *HTML* debug page or a rendered
*HTML* error page. When you're working with an API client, neither of those
options are particularly friendly/natural, especially if you need to extract
information to present to the user.

``microapi`` improves on this by intercepting errors, and rendering a
*JSON-based* API error response instead! If the lookup fails, the user will get
an error like::

    {
        "success": False,
        "errors": [
            "Blog post not found"
        ]
    }

Even if we hadn't explicitly added ``try/except`` handling, under the hood,
``microapi`` would've rendered a similar error including the exception message.

You can manually call ``self.render_error(...)`` as many times as you want in
your view code, and you can supply either a single error string, or a list of
error strings! This can be great for validation situations, or when multiple
conditions failed.

The Use of ``serialize(...)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The final notable change is the call to ``self.serialize(post)``.

Previously, in the list endpoint, we just quietly called
``self.serialize_many(posts)`` & didn't really talk about serialization, letting
``microapi`` just handle things for us.

The rule of thumb here is to call ``serialize(model_obj)`` when it's a *single*
instance, and calling ``serialize_many(queryset_or_list)`` when it's a
*collection* of instances to serialize.

.. note:: ``serialize_many(...)`` just iterates & makes calls to
    ``serialize(...)``. So you can customize just the detail serialization in
    ``serialize``, & the list version coming from ``serialize_many`` will stay
    in-sync.

This all leads us to a slight tangent: serialization in general.


Tangent: Serialization
----------------------

When it comes to the format of data entering/leaving an API, there are a wide
range of viewpoints. Some people subscribe to a minimalist view, meaning
returning a small/flat structure of the data (which can lead to many simple
requests). Others prefer deep/rich structures, including related data structures
(a single request with a large/complex response). Still others want follow
things like `HATEOAS <https://en.wikipedia.org/wiki/HATEOAS>`_ & return URLs
to resources instead of PKs or nested structures.

To combat assumptions (& honestly complex feature bloat), ``microapi`` takes a
simplistic approach to the default serialization, then makes it easy to
extend/override serialization to meet your needs.

By default, ``microapi`` includes a ``ModelSerializer``, which we've been
conveniently/quietly using via ``ApiView.serialize(...)`` /
``ApiView.serialize_many(...)``.

``ModelSerializer`` will accept a model instance, collect all **concrete**
fields, and return a dictionary representation of that data. It will **NOT**
collect/return:

* related fields/data
* generated fields
* virtual fields

While this is limited by default, this prevents excessively leaning on PKs or
too-deeply-nested situations, as well as a whole host of edge-cases. It's also
easily extended, as we're about to see.


Adding Author Information
-------------------------

Let's change things so that the author information is included in the API. For
our uses, since ``author`` is a single related object that will always be
present, we want to include a nested representation of it::

    # blog/api.py
    from microapi import ApiView

    from .models import BlogPost


    class BlogPostListView(ApiView):
        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })


    class BlogPostDetailView(ApiView):
        # We're adding code here!
        def serialize(self, obj):
            data = super().serialize(obj)
            data["author"] = self.serializer.to_dict(obj.author)
            return data

        def get(self, request, pk):
            try:
                post = BlogPost.objects.get(pk=pk)
            except BlogPost.DoesNotExist:
                return self.render_error("Blog post not found")

            return self.render({
                "success": True,
                "post": self.serialize(post),
            })

To start with, we override the ``BlogPostDetailView.serialize(...)`` method.
We'll call ``super().serialize(...)`` to get the default data from ``microapi``.

Then we embelish the resulting ``dict`` to add the ``author`` key, and use the
``self.serializer.to_dict(...)`` to give us a serialized version of the related
``User`` object. Then finally we return the newly-serialized data.

In this way, we retain strong control over how we represent data in our API,
while trying to keep the implementation as clean/simple as possible.

Now when the user requests something like
https://localhost:8000/api/v1/posts/1/, they get::

    {
        "success": True,
        "post": {
            "id": 1,
            "title": "Hello, world!",
            "slug": "hello-world",
            "author": {
                "id": 1,
                "username": "daniel",
                "email": "daniel@toastdriven.com",
                "first_name": "Daniel",
                "last_name": "",
                "password": "OMG_REDACTED_THIS_IS_SUPER_BAD",
                "is_superuser": True,
                "is_staff": True,
                "is_active": True,
                "date_joined": "2023-12-19-T11:03:19.000-0600",
                "last_login": "2024-01-09-T20:10:55.000-0600"
            },
            "content": "My first post to my blog!",
            "created": "2024-01-09-T20:10:55.000-0600",
            "updated": "2024-01-09-T20:10:55.000-0600",
        }
    }

While this is a substantial improvement, we've got a **BIG** problem: because
we're naively serializing ``User``, we're **leaking** private user information!
Things like ``password``, ``is_superuser``, ``is_staff``, ``last_login``
shouldn't be generally be included in an API!

Fortunately, this is easy to remedy::

    class BlogPostDetailView(ApiView):
        def serialize(self, obj):
            data = super().serialize(obj)
            # We're changing up this line.
            data["author"] = self.serializer.to_dict(
                obj.author,
                # We can supply `exclude` here & provide a list of fields that
                # should not be included in the serialized representation.
                exclude=[
                    "password",
                    "is_superuser",
                    "is_staff",
                    "date_joined",
                    "last_login",
                ]
            )
            return data

Refresh https://localhost:8000/api/v1/posts/1/, and now the user gets a
much-safer & more reasonable set of data::

    {
        "success": True,
        "post": {
            "id": 1,
            "title": "Hello, world!",
            "slug": "hello-world",
            "author": {
                "id": 1,
                "username": "daniel",
                "email": "daniel@toastdriven.com",
                "first_name": "Daniel",
                "last_name": ""
            },
            "content": "My first post to my blog!",
            "created": "2024-01-09-T20:10:55.000-0600",
            "updated": "2024-01-09-T20:10:55.000-0600",
        }
    }

Finally, let's say we want this author information in the list view as well.
And because we've got a custom ``User`` model, we want to play it safe & show
only an approved list of fields::

    # blog/api.py
    from microapi import ApiView

    from .models import BlogPost


    # New code starts here!
    def serialize_author(serializer, author):
        # Rather than lean on the serializer, there's nothing stopping us from
        # just constructing our own dict of data.
        # In this case, should new fields get added in the future, this prevents
        # potentially-sensitive leaks of data.
        return {
            "id": author.id,
            "username": author.username,
            "email": author.email,
            "first_name": author.first_name,
            "last_name": author.last_name,
        }


    # No need to define a custom class or anything. Any callable that returns
    # JSON-serializable data is good enough.
    def serialize_post(serializer, post):
        data = serializer.to_dict(post)
        data["author"] = serialize_author(serializer, post.author)
        return data


    class BlogPostListView(ApiView):
        # Newly overridden!
        def serialize(self, obj):
            return serialize_post(obj)

        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })


    class BlogPostDetailView(ApiView):
        # Replacing our old overridden code!
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

Now our list & detail endpoints have matching data, and we
:abbr:`DRY (Don't Repeat Yourself)`'ed up the code to create a single way we
serialize both authors & posts.


Creating Data
-------------

Up until now, we've been only working on a read-only version of the API that
solely responds to ``HTTP GET``. But it'd be nice to be able to *create* new
blog posts via the API.

In most RESTful applications, the expected way to handle creating new data is to
perform an ``HTTP POST`` to the *list* endpoint, so let's add that::

    # blog/api.py
    # This import changed!
    from microapi import (
        ApiView,
        http,
    )

    from .models import BlogPost


    # Omitting serialization for readability.
    # ...
    # Leave it there!


    class BlogPostListView(ApiView):
        def serialize(self, obj):
            return serialize_post(obj)

        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })

        # Here's the newly added code!
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

We've added a new ``post`` method to ``BlogPostListView``. The other new bits
here are the use of ``read_json(request)`` & ``serializer.from_dict(...)``.

``microapi`` includes an ``ApiView.read_json(request)`` method, which makes it
easy to extract a JSON payload from a request body. This is similar to how
you might use ``request.POST`` in regular application code.

The other noteworthy code,
``post = self.serializer.from_dict(BlogPost(), data)``, is a bit more involved,
so let's deconstruct what's going on.

``ModelSerializer`` includes a ``from_dict(model_obj, data)`` method, which
takes a ``dict`` of data & tries to assign the values to fields on a ``Model``
instance. Since we've already grabbed the request ``data`` fromthe JSON, and
we're creating a new model object (``BlogPost()``), we can just hand those two
off to ``self.serializer.from_dict(BlogPost(), data)`` & it will populate that
fresh model instance for us.

Assign on the ``author`` to the user that ``POST``'ed the data, remember to
**save**, and then we return a success message with the newly-created data. We
can supply the ``http.CREATED`` status code to ensure the resulting response has
a ``201 Created`` HTTP status code associated with it!


Updating & Deleting Data
------------------------

Finally, let's add updating & deleting data. These are pretty straight-forward
& largely just combine things we've already seen::

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

        # New code starts here!
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
            }, status_code=http.UPDATED)

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

We add a ``put`` method to handle updating an existing object via ``HTTP PUT``
to the detail endpoint, and a ``delete`` method to handle deleting an existing
object via ``HTTP DELETE``.

Both lookup/fetch the post as we have before. For the update, we read the JSON
payload from the ``request`` body & update the object just like in the ``POST``
example. And for the delete, all we need to do is delete the model via the ORM.


Final Code
----------

When we've finished, our final API code should look like::

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
            }, status_code=http.UPDATED)

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

And with that, plus the two URLconfs you added long ago, you have a RESTful API
for inspecting/managing blog posts in your application! 🎉


Next Steps
----------

This represents ~90%+ of the daily usage of ``microapi``, but the library
does include a handful of other tools/utilities to make crafting APIs
easier. Information on these can be found in the other Usage guides or the
Api docs.

Enjoy & happy API creation!
