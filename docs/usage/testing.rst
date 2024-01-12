Testing
=======


Example Endpoints
-----------------

We'll start with the similar code from the :doc:`Quick Start <quickstart>`::

    # blog/api.py
    from django.contrib.auth.decorators import login_required

    from microapi import (
        ApiView,
        http,
    )

    from .models import BlogPost


    class BlogPostView(ApiView):
        def get(self, request):
            posts = BlogPost.objects.all().order_by("-created")
            return self.render({
                "success": True,
                "posts": self.serialize_many(posts),
            })

        @login_required
        def post(self, request):
            data = self.read_json(request)

            # TODO: Validate the data here.

            post = self.serializer.from_dict(BlogPost(), data)
            post.save()

            return self.render({
                "success": True,
                "post": self.serialize(post),
            }, status_code=http.CREATED)


Adding Tests
------------

TBD.
