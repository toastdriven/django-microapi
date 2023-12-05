from django.urls import path

from .views import (
    BlogPostListView,
    BlogPostDetailView,
)

urlpatterns = [
    path("api/v1/posts/", BlogPostListView.as_view()),
    path("api/v1/posts/<int:post_id>/", BlogPostDetailView.as_view()),
]
