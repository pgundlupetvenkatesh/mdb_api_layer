"""
Shared fixtures and configuration for Pact consumer-driven contract tests.

Centralizes the Pact mock-server settings and the per-test ``pact`` /
``pact_movies_api`` / ``pact_address`` fixtures so each contract module only
declares its interactions. Test classes set a ``consumer_name`` class
attribute naming the consumer side of the contract; the provider is shared.
"""

import pytest
from pact import Pact

from api.movies_api import MoviesAPI

# Pact mock server config
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234
PACT_DIR = "tests/pacts"

# Shared provider name so every contract file's interactions merge under a
# single provider contract.
PACT_PROVIDER = "api_pvd"


@pytest.fixture
def pact(request):
    """
    Provide a fresh Pact instance per test and write the contract on teardown.

    A new Pact is created per test because once ``pact.serve()`` runs and its
    context manager exits the handle is finalized, so no further interactions
    can be added. The consumer name is read from the test class's
    ``consumer_name`` attribute; the provider is the API under contract.

    :yields: Configured Pact instance ready for interaction definition.
    """
    consumer = getattr(request.cls, "consumer_name", None)
    if not consumer:
        raise AttributeError(
            f"{request.cls.__name__} must set a 'consumer_name' class attribute"
        )
    pact = Pact(consumer, PACT_PROVIDER)
    yield pact

    # Write/merge the contract file after each test
    pact.write_file(directory=PACT_DIR)


@pytest.fixture
def pact_movies_api():
    """
    Provide a fresh MoviesAPI client for a contract test.

    Returns the client with its default (real TMDB) base URL. Each test
    repoints ``base_url`` at the Pact mock server *after* ``pact.serve()``
    starts, because the mock server's URL/port aren't known until then.
    """
    return MoviesAPI()


@pytest.fixture
def pact_address():
    """Return the ``(host, port)`` the Pact mock server should bind to."""
    return PACT_MOCK_HOST, PACT_MOCK_PORT