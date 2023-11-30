`django-microapi` Quick Start
=============================

Installation
------------

The only requirement is Django (most recent releases should work fine).

::

    $ pip install django-microapi


Usage
-----

::

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

            # Use the included `ModelSerializer` to load the user-provided data
            # into a new `BlogPost`.
            serializer = ModelSerializer()
            post = serializer.from_dict(BlogPost(), data)
            # Don't forget to save!
            post.save()

            return self.render({
                "success": True,
                "post": self.serialize(post),
            })
