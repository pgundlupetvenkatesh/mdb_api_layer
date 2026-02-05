import yaml
from pathlib import Path

def load_test_data(file_name: str) -> dict:
    """
        Load test data from a YAML file and apply default values.

        Reads a YAML file from the same directory as this module and applies
        any defined defaults to test case entries.

        :param file_name: Name of the YAML file containing test data.
        :return: Parsed data from the YAML file with defaults applied.
        :raises FileNotFoundError: If the specified file does not exist.
        :raises yaml.YAMLError: If the file contains invalid YAML.
        """
    data_path = Path(__file__).parent / file_name
    with open(data_path, 'r') as file:
        data = yaml.safe_load(file)

        _apply_defaults(data)
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