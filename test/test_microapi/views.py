from microapi import ApiView
from microapi import http

from .models import BlogPost


class OhHellNoError(Exception):
    pass


class BlogPostListView(ApiView):
    bubble_exceptions = True

    def get(self, request):
        posts = BlogPost.objects.all().order_by("-published_on")
        return self.render(
            {
                "success": True,
                "posts": self.serialize_many(posts),
            }
        )

    def post(self, request):
        data = self.read_json(request)
        new_post = BlogPost()

        self.serializer.from_dict(new_post, data)

        new_post.published_by = request.user
        new_post.save()

        return self.render(
            {
                "success": True,
                "post": self.serialize(new_post),
            },
            status_code=http.CREATED,
        )

    def delete(self, request):
        # This is a supported method, but we want to test exception bubbling.
        # So raise an unhandled exception!
        raise OhHellNoError("I don't think so.")


class BlogPostDetailView(ApiView):
    # Not an HTTP method.
    def get_blog_post(self, post_id):
        return BlogPost.objects.get(pk=post_id)

    def get(self, request, post_id):
        try:
            post = self.get_blog_post(post_id)
        except BlogPost.DoesNotExist:
            return self.render_error("Post does not exist")

        return self.render(
            {
                "success": True,
                "post": self.serialize(post),
            }
        )

    def put(self, request, post_id):
        data = self.read_json(request)
        post = self.get_blog_post(post_id)

        self.serializer.from_dict(post, data, strict=True)
        post.save()

        return self.render(
            {
                "success": True,
                "post": self.serialize(post),
            },
            status_code=http.ACCEPTED,
        )

    def delete(self, request, post_id):
        post = self.get_blog_post(post_id)
        post.delete()
        return self.render({}, status_code=http.NO_CONTENT)
