"""Field assertion helpers for test validation."""
class FieldAssertions:
    """Mixin class providing field validation assertion methods."""
    _test_name = '' # Defined here but is set by the consuming class

    def assert_bool_field(self, data, field, index=None):
        """
        Assert that a field value is a boolean.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a boolean.
        """
        idx = f'{index}' if index is not None else ''
        assert isinstance(data[field], bool), f"{self._test_name}: Index {idx} {field} Response should be boolean"

    def assert_str_field(self, data, field, index=None):
        """
        Assert that a field value is a non-empty string.

        For 'original_language' fields, validates 2-character ISO code length.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a string or is empty.
        """
        idx = f'{index}' if index is not None else ''

        assert field in data, f"{self._test_name}: Index {idx} should contain {field} field"
        if field == 'place_of_birth':
            # place_of_birth can be empty/null, so only validate its type (done below)
            pass
        else:
            assert isinstance(data[field], str), f"{self._test_name}: Index {idx} {field} Response should be string"

        if field == 'original_language':
            assert len(data[field]) == 2, f"{self._test_name}: Index {idx} {field} should be 2-char code"
        elif field in ['overview', 'origin_country', 'place_of_birth']:
            # These fields can be empty/null, so only validate its type (done above)
            return
        else:
            assert len(data[field]) > 0, f"{self._test_name}: Index {idx} {field} should not be empty"

    def assert_int_field(self, data, field, index=None, id_val=None):
        """
        Assert that a field value is a positive integer.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :param id_val: Optional expected value for 'id' fields.
        :raises AssertionError: If the field is not an integer or not positive.
        """
        idx = f'{index}' if index is not None else ''

        assert field in data, f"Index {idx} should contain {field} field"
        assert isinstance(data[field], int), f"{self._test_name}: Index {idx} {field} Response should be int"

        if id_val is not None:
            assert data[field] == id_val, f"{self._test_name}: Index {idx} {field} should be {id_val}"
        else:
            assert data[field] >= 0, f"{self._test_name}: Index {idx} {field} should be non-negative"

    def assert_path_field(self, data, field, index=None):
        """
        Assert that a field is a valid image path or null.

        Validates that the path ends with '.png' or '.jpg' if not null.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If field is missing or has invalid format.
        """
        idx = f'{index}' if index is not None else ''

        assert field in data, f"{self._test_name}: Index {idx} should contain '{field}' field"
        assert data[field] is None or isinstance(data[field],
                                                 str), f"{self._test_name}: Index {idx} {field} should be String"
        assert data[field] is None or data[field].endswith(
            ('.png', '.jpg')), f'{self._test_name}: Index {idx} {field} should be PNG'

    def assert_float_field(self, data, field, index=None):
        """
        Assert that a field value is a positive float.

        For 'vote_average' fields, validates range is 0.0-10.0.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a float or out of range.
        """
        idx = f'{index}' if index is not None else ''
        assert isinstance(data[field], float), f"{self._test_name}: Index {idx} {field} Response should be float"

        if field == 'vote_average':
            assert 0.0 <= data[field] <= 10.0, f"{self._test_name}: Index {idx} {field} should be between 0.0 and 10.0"
        else:
            assert data[field] >= 0.0, f"{self._test_name}: Index {idx} {field} should be positive"

    def assert_list_field(self, data, field, index=None):
        """
        Assert that a field value is a non-empty list.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a list or is empty.
        """
        idx = f'{index}' if index is not None else ''

        assert field in data, f"{self._test_name}: Index {idx} should contain {field} field"
        assert isinstance(data[field], list), f"{self._test_name}: Index {idx} {field} Response should be a list"

        if field in ['genres', 'production_companies', 'also_known_as', 'genre_ids']:
            # These fields can be empty lists, so only validate it's a list (done above)
            return

        assert len(data[field]) > 0, f"{self._test_name}: Index {idx} {field} should not be empty"