import datetime

from django.utils.timezone import make_aware

from microapi.tests import (
    ApiTestCase,
    check_response,
)

from ..models import (
    BlogPost,
    User,
)
from ..views import (
    BlogPostListView,
    BlogPostDetailView,
    OhHellNoError,
)


class BlogPostApiTestCase(ApiTestCase):
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

    def test_posts_get_list(self):
        req = self.create_request(
            "/api/v1/posts/",
        )
        resp = self.make_request(BlogPostListView, req)
        self.assertOK(resp)

        data = check_response(resp)
        self.assertTrue(data["success"])
        self.assertTrue(len(data["posts"]), 2)
        self.assertEqual(data["posts"][0]["slug"], "life-update")
        self.assertEqual(data["posts"][1]["slug"], "hello-world")

    def test_posts_post_list(self):
        # Sanity check.
        self.assertEqual(BlogPost.objects.count(), 2)

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

        data = check_response(resp)
        self.assertTrue(data["success"])
        self.assertTrue(data["post"]["title"], "Cat Pictures")
        self.assertTrue(data["post"]["slug"], "cat-pictures")
        self.assertTrue(data["post"]["content"], "All the internet is good for.")

        self.assertEqual(BlogPost.objects.count(), 3)
        post = BlogPost.objects.get(slug="cat-pictures")
        self.assertEqual(post.published_by.pk, self.user.pk)
        self.assertEqual(post.published_on.year, 2023)
        self.assertEqual(post.published_on.month, 12)
        self.assertEqual(post.published_on.day, 5)
        self.assertEqual(post.published_on.hour, 17)

    def test_bubble_exceptions(self):
        req = self.create_request(
            f"/api/v1/posts/",
            method="delete",
            user=self.user,
        )

        with self.assertRaises(OhHellNoError):
            self.make_request(BlogPostListView, req)

    def test_get_detail(self):
        req = self.create_request(
            f"/api/v1/posts/{self.post_1.pk}/",
        )
        resp = self.make_request(BlogPostDetailView, req, post_id=self.post_1.pk)
        self.assertOK(resp)

        data = check_response(resp)
        self.assertTrue(data["success"])
        self.assertEqual(data["post"]["slug"], "hello-world")

    def test_put_detail(self):
        req = self.create_request(
            f"/api/v1/posts/{self.post_1.pk}/",
            method="put",
            data={
                "content": "Fixed a typo.",
            },
            user=self.user,
        )
        resp = self.make_request(BlogPostDetailView, req, post_id=self.post_1.pk)
        self.assertAccepted(resp)

        data = check_response(resp)
        self.assertTrue(data["success"])
        self.assertEqual(data["post"]["slug"], "hello-world")
        # The only field that should've been touched.
        self.assertEqual(data["post"]["content"], "Fixed a typo.")

    def test_delete_detail(self):
        # Sanity check.
        self.assertEqual(BlogPost.objects.count(), 2)

        req = self.create_request(
            f"/api/v1/posts/{self.post_1.pk}/",
            method="delete",
            user=self.user,
        )
        resp = self.make_request(BlogPostDetailView, req, post_id=self.post_1.pk)
        self.assertNoContent(resp)

        self.assertEqual(BlogPost.objects.count(), 1)

        with self.assertRaises(BlogPost.DoesNotExist):
            BlogPost.objects.get(slug="hello-world")

    def test_no_patch_shortcuts(self):
        with self.assertRaises(ValueError) as err:
            self.create_request(
                f"/api/v1/posts/{self.post_1.pk}/",
                method="patch",
                data={
                    "nope": "nopenope",
                },
                user=self.user,
            )

            self.assertTrue("does not support PATCH" in str(err))
