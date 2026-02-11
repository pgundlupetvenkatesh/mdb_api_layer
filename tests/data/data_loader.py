import yaml
from pathlib import Path

from tests.helpers.test_data_generators import *

# Map YAML placeholder strings to generator functions
GENERATORS = {
    '$random_rating': random_rating,
    '$random_invalid_rating': random_invalid_rating,
    '$random_movie_id': pick_random_movie_id
}

def load_test_data(file_name: str) -> dict:
    """
        Load test data from a YAML file and apply default values.

        Reads a YAML file from the same directory as this module and applies
        any defined defaults to test case entries. Also processes dynamic
        placeholders like '$random_rating' by calling the mapped generator functions.

        :param file_name: Name of the YAML file containing test data.
        :return: Parsed data from the YAML file with defaults applied.
        :raises FileNotFoundError: If the specified file does not exist.
        :raises yaml.YAMLError: If the file contains invalid YAML.
        """
    data_path = Path(__file__).parent / file_name
    with open(data_path, 'r') as file:
        data = yaml.safe_load(file)

        _apply_defaults(data)
        _process_generators(data)
        return data

def _apply_defaults(data: dict) -> None:
    """
    Apply default values to test data sections in-place.

    Iterates through each section in the data dictionary. If a section
    contains a 'defaults' key, those default values are applied to each
    test case in the corresponding category using setdefault (existing
    values are not overwritten).

    Global defaults (top-level 'defaults' key) are applied to ALL test cases
    across all sections.

    Expected YAML structure:
        defaults:              # Global defaults applied to all test cases
          key: default_value
        section_name:
          defaults:            # Section-specific defaults
            category_name:
              key: default_value
          category_name:
            - test_case_1
            - test_case_2

    :param data: Dictionary of test data to modify. Modified in-place.
    :return: None. The input dictionary is modified directly.
    """
    if not isinstance(data, dict):
        return

    # Extract global defaults
    global_defaults = data.pop('defaults', {}) or {}

    for section, content in data.items():
        if not isinstance(content, dict):
            continue    # Skip non-dict values

        defaults = content.pop('defaults', None)

        # Apply defaults to each category in the section
        for category, test_cases in content.items():
            if not isinstance(test_cases, list):
                continue

            # Get category-specific defaults
            category_defaults = {}
            if isinstance(defaults, dict) and category in defaults:
                category_defaults = defaults[category]

            for test_case in test_cases:
                if isinstance(test_case, dict):
                    # Apply global defaults first
                    for k, v in global_defaults.items():
                        test_case.setdefault(k, v)
                    # Apply category-specific defaults (can override global if same key)
                    for k, v in category_defaults.items():
                        test_case.setdefault(k, v)


def _process_generators(data: dict) -> None:
    """
    Process generator placeholders in test data.

    Recursively searches for string values matching generator placeholders
    (e.g., '$random_rating') and replaces them with generated values.

    :param data: Dictionary of test data to modify. Modified in-place.
    :return: None. The input dictionary is modified directly.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value in GENERATORS:
                data[key] = GENERATORS[value]()
            elif isinstance(value, dict):
                _process_generators(value)
            elif isinstance(value, list):
                _process_generators_list(value)
    elif isinstance(data, list):
        _process_generators_list(data)


def _process_generators_list(data: list) -> None:
    """
    Process generator placeholders in a list.

    :param data: List to process. Modified in-place.
    """
    for i, item in enumerate(data):
        if isinstance(item, str) and item in GENERATORS:
            data[i] = GENERATORS[item]()
        elif isinstance(item, dict):
            _process_generators(item)
        elif isinstance(item, list):
            _process_generators_list(item)
