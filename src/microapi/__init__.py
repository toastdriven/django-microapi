"""
django-microapi
===============

A tiny library to make writing CBV-based APIs easier in Django.

Essentially, this just provides some sugar on top of the plain old
`django.views.generic.base.View` class, all with the intent of making handling
JSON APIs easier (without the need for a full framework).
"""
from .exceptions import (
    ApiError,
    InvalidFieldError,
    DataValidationError,
)
from .serializers import ModelSerializer
from .views import ApiView


__author__ = "Daniel Lindsley"
__license__ = "New BSD"
__version__ = "1.1.0"

# For convenience...
__ALL__ = [
    ApiView,
    ModelSerializer,
    ApiError,
    InvalidFieldError,
    DataValidationError,
]
