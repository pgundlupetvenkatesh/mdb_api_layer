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

    Expected YAML structure:
        section_name:
          defaults:
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

    for section, content in data.items():
        if not isinstance(content, dict):
            continue    # Skip non-dict values

        defaults = content.pop('defaults', None)
        if not isinstance(defaults, dict):
            continue

        for category, default_values in defaults.items():
            if category in content and isinstance(content[category], list):
                for test_case in content[category]:
                    if isinstance(test_case, dict):
                        for k, v in default_values.items():
                            test_case.setdefault(k, v)