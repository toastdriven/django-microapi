# django-microapi

[![Documentation Status](https://readthedocs.org/projects/django-microapi/badge/?version=latest)](https://django-microapi.readthedocs.io/en/latest/?badge=latest)

A tiny library to make writing CBV-based APIs easier in Django.

Essentially, this just provides some sugar on top of the plain old `django.views.generic.base.View` class, all with the intent of making handling JSON APIs easier (without the need for a full framework).


## Usage

```python
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
```


## Installation

```bash
$ pip install django-microapi
```


## Rationale

There are a lot of API frameworks out there (hell, I [built](https://tastypieapi.org/) [two](https://github.com/toastdriven/restless) of them). But for many tasks, they're either [overkill](https://en.wikipedia.org/wiki/HATEOAS) or just too opinionated.

So `django-microapi` is kind of the antithesis to those. With the exception of a tiny extension to `View` for nicer errors, it doesn't call **ANYTHING** automatically. Other than being JSON-based, it doesn't have opinions on serialization, or validation, or URL structures.

You write the endpoints you want, and `microapi` brings some conveniences to the table to make writing that endpoint as simple as possible _without_ assumptions.

I've long had a place in my heart for the simplicity of Django's function-based views, as well as the conveniences of `django.shortcuts`. `microapi` tries to channel that love/simplicity.


## API Docs

https://django-microapi.rtfd.io/


## License

New BSD
