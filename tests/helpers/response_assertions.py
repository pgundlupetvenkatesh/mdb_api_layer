def assert_http_response(response, exp_val):
    """
    Assert common HTTP response properties.

    :param response: The HTTP response object to validate.
    :param exp_val: A dictionary containing expected values:
        - 'exp_req_method': Expected HTTP method (e.g., 'GET').
        - 'exp_status_code': Expected HTTP status code (e.g., 200).
        - 'exp_content_type': Expected content type substring (e.g., 'application/json').
        - 'exp_max_elp_seconds': Maximum allowed response time in seconds (e.g., 2).
        - 'exp_url_contains': Substring that should be present in the response URL (e.g., movie ID).
    :raises AssertionError: If any validation fails.
    """
    exp_req_method = exp_val['exp_req_method']

    assert response.request == exp_req_method, f"HTTP method is not {exp_req_method}"
    assert response.status_code == exp_val['exp_status_code'], f"returned status code is not {exp_val['exp_status_code']}"
    assert exp_val['exp_content_type'] in response.headers['Content-Type'], 'response is not in JSON format'
    assert response.elapsed_seconds < exp_val['exp_max_elp_seconds'], \
        f"Actual response time is greater than expected. Actual: {response.elapsed_seconds} seconds, Expected: < {exp_val["exp_max_elp_seconds"]} seconds"
    assert exp_val['exp_url_contains'] in response.url, f"Response url should contain movie ID '{exp_val['exp_url_contains']}'"
    assert response.reason == exp_val['exp_req_reason'], f"Response reason should be '{exp_val['exp_req_reason']}' but it's '{response.reason}'"

def assert_get_metadata(response, case, url_contains):
    """
    Assert standard GET response metadata from a parametrized test case.

    Builds the expected-values dict from a test case (valid or invalid)
    and delegates to ``assert_http_response``, keeping the metadata key
    names in one place.

    :param response: APIResponse returned by the client.
    :param case: Parametrized test data dict (expects ``status_code``,
                 ``exp_max_elp_secs``, ``exp_get_req_method``,
                 ``exp_content_type``, ``reason``).
    :param url_contains: Substring expected in the response URL.
    """
    assert_http_response(response, {
        'exp_status_code': case['status_code'],
        'exp_max_elp_seconds': case['exp_max_elp_secs'],
        'exp_req_method': case['exp_get_req_method'],
        'exp_content_type': case['exp_content_type'],
        'exp_url_contains': str(url_contains),
        'exp_req_reason': case['reason']
    })