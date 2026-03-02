import pytest
from jsonschema import validate
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")

class TestDetails(FieldAssertions):
    @pytest.fixture(autouse=True)
    def _store_test_name(self, request):
        """
        Fixture to capture and store the current test name.

        Automatically runs before each test method (autouse=True) and stores
        the test name in self._test_name for use in assertion messages.

        :param request: Pytest request fixture providing test context.
        """
        self._test_name = request.node.name

    @pytest.mark.parametrize('person_details', TEST_DATA['get_person_details']['valid'])
    def test_get_person_details(self, get_api_instance, load_schema, person_details):
        """
        Test fetching person details with valid data.

        Validates that the response contains expected fields and matches the
        defined JSON schema for person details.

        :param person_details: Dictionary containing test parameters for a valid case.
        """
        logger.info(f"Random person ID picked: {person_details['person_id']}")
        people_api = get_api_instance('people_api')
        response = people_api.get_person_details(person_details['person_id'])
        res_body = response.data

        assert_http_response(response, {
            'exp_status_code': person_details['status_code'],
            'exp_max_elp_seconds': person_details['exp_max_elp_secs'],
            'exp_req_method': person_details['exp_get_req_method'],
            'exp_content_type': person_details['exp_content_type'],
            'exp_url_contains': 'person',
            'exp_req_reason': person_details['reason']
        })

        # response structure validation
        self.assert_list_field(res_body, 'also_known_as')

        self.assert_str_field(res_body, 'biography')
        self.assert_str_field(res_body, 'birthday')
        self.assert_str_field(res_body, 'imdb_id')
        self.assert_str_field(res_body, 'known_for_department')
        self.assert_str_field(res_body, 'name')
        self.assert_str_field(res_body, 'place_of_birth')
        self.assert_path_field(res_body, 'profile_path')

        self.assert_bool_field(res_body, 'adult')

        self.assert_int_field(res_body, 'gender')
        self.assert_int_field(res_body, 'id')
        self.assert_float_field(res_body, 'popularity')

        # Validate against JSON schema
        validate(instance=res_body, schema=load_schema('person_details_schema'))