from collections import OrderedDict

from django.db.models.fields.related import RelatedField

from .exceptions import InvalidFieldError


class ModelSerializer:
    """
    A stupid-simple object to handle serializing/deserializing Model data.

    If you have even the slightest of complex needs, you're better off handling
    serialization manually.
    """

    def collect_field_names(self, model):
        """
        Given a Model instance, collects all the field names from it.

        This includes any parent fields. It excludes:
        * Related fields
        * Generated fields
        * Virtual fields

        Args:
            model (Model): A Django Model instance (not the class).

        Returns:
            list: A sorted list of all field names.
        """
        field_names = set()

        for field in model._meta.fields:
            # Exclude exceptional (Related, Generated, Virtual) fields.
            if field.column is None or getattr(field, "generated", False):
                continue

            if isinstance(field, RelatedField):
                continue

            field_names.add(field.attname)

        # Sort the field list in alphabetical order.
        # While not strictly necessary, we're talking about a relatively small
        # number of fields, and nicer readability for consumers.
        return sorted(field_names)

    def to_dict(self, model, exclude=None):
        """
        Converts a populated Model's fields/values into a plain dictionary.

        Args:
            model (Model): A populated Model instance.
            exclude (list): A list of fields to exclude from the final dict.
                Default is `[]`.

        Returns:
            OrderedDict: A dictionary of the field names/values.
        """
        if exclude is None:
            exclude = []

        # Use an ordered dict, as it'll preserve the sorted field order when
        # it's time to serialize the JSON.
        data = OrderedDict()
        field_list = self.collect_field_names(model)

        for field_name in field_list:
            data[field_name] = getattr(model, field_name)

        for exclude_name in exclude:
            data.pop(exclude_name, None)

        return data

    def from_dict(self, model, data, strict=False):
        """
        Loads data from a dictionary onto a Model instance.

        If there are keys in the data that you do **NOT** want populated on the
        Model (such as primary keys, "private" fields, etc.), you should `pop`
        those values before passing to this method.

        Args:
            model (Model): A Model instance.
            data (dict): The data provided by a user.
            strict (bool): (Optional) If `True`, requires all keys in the data
                to match to an existing Model field. Default is `False`.

        Returns:
            Model: The populated (but unsaved) model instance.
        """
        field_list = self.collect_field_names(model)

        for key, value in data.iteritems():
            if strict and key not in field_list:
                raise InvalidFieldError(
                    f"{key} not found on {model.__class__.__name__}"
                )

            setattr(model, value)

        return model
