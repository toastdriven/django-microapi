.. django-microapi documentation master file, created by
   sphinx-quickstart on Thu Nov 30 16:46:53 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

`django-microapi` Documentation
===============================

A tiny library to make writing CBV-based APIs easier in Django.

Essentially, this just provides some sugar on top of the plain old
`django.views.generic.base.View` class, all with the intent of making handling
JSON APIs easier (without the need for a full framework).

.. toctree::
   :maxdepth: 2
   :caption: Usage:

   usage/quickstart

.. toctree::
   :maxdepth: 2
   :caption: API Docs:

   api/views
   api/serializers
   api/exceptions


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
