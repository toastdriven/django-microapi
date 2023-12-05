import datetime

from django.test import TestCase
from django.utils.timezone import make_aware

from microapi import ModelSerializer
from microapi.exceptions import InvalidFieldError

from ..models import (
    BlogPost,
    User,
)


class ModelSerializerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.serializer = ModelSerializer()
        self.user = User.objects.create_user(
            "testmctest",
            "test@mctest.com",
            "testpass",
        )

    def test_collect_field_names_post(self):
        names = self.serializer.collect_field_names(BlogPost)
        self.assertEqual(names, ["content", "id", "published_on", "slug", "title"])

    def test_collect_field_names_user(self):
        serializer = ModelSerializer()
        names = serializer.collect_field_names(User)
        self.assertEqual(
            names,
            [
                "date_joined",
                "email",
                "first_name",
                "id",
                "is_active",
                "is_staff",
                "is_superuser",
                "last_login",
                "last_name",
                "password",
                "username",
            ],
        )

    def test_to_dict(self):
        # Sanity check.
        self.assertEqual(BlogPost.objects.count(), 0)

        post = BlogPost.objects.create(
            title="Hello, World!",
            content="My first post! *SURELY*, it won't be the last...",
            published_by=self.user,
            published_on=make_aware(
                datetime.datetime(2023, 11, 28, 9, 26, 54, 123456),
                timezone=datetime.timezone.utc,
            ),
        )

        data = self.serializer.to_dict(post)

        self.assertEqual(
            [key for key in data],
            ["content", "id", "published_on", "slug", "title"],
        )

        # To prevent test failures due to whatever PK is assigned.
        data.pop("id")

        self.assertEqual(
            data["content"], "My first post! *SURELY*, it won't be the last..."
        )
        self.assertEqual(data["published_on"].year, 2023)
        self.assertEqual(data["published_on"].month, 11)
        self.assertEqual(data["published_on"].day, 28)
        self.assertEqual(data["slug"], "hello-world")
        self.assertEqual(data["title"], "Hello, World!")

    def test_from_dict(self):
        post = BlogPost()

        self.serializer.from_dict(
            post,
            {
                "title": "Life Update",
                "content": "So, it's been awhile...",
            },
        )

        post.published_by = self.user
        post.save()

        self.assertEqual(post.content, "So, it's been awhile...")
        self.assertEqual(post.slug, "life-update")
        self.assertEqual(post.title, "Life Update")

    def test_from_dict_strict_fail(self):
        post = BlogPost()

        with self.assertRaises(InvalidFieldError):
            self.serializer.from_dict(
                post,
                {
                    "lmao": "so_invalid",
                    "title": "Life Update",
                    "content": "So, it's been awhile...",
                },
                strict=True,
            )

    def test_from_dict_strict_success(self):
        post = BlogPost()

        # This shouldn't raise any exceptions.
        # If so, we're good & test passes.
        self.serializer.from_dict(
            post,
            {
                "title": "Life Update",
                "content": "So, it's been awhile...",
            },
            strict=True,
        )
