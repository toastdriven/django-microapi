from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


User = get_user_model()


class BlogPost(models.Model):
    title = models.CharField(max_length=64)
    slug = models.SlugField(blank=True, unique=True, db_index=True)
    content = models.TextField(blank=True, default="")
    published_by = models.ForeignKey(
        User,
        related_name="blog_posts",
        on_delete=models.CASCADE,
    )
    published_on = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        return super().save(*args, **kwargs)
