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
PACT_MOCK_PORT = 0  # 0 = let the OS pick a free port (avoids collisions under parallel runs); tests read srv.url
PACT_DIR = "tests/pacts"

# Shared consumer/provider identities. Both are constant across every contract
# module so all interactions merge into a single consumer->provider contract
# (``mdb_api_layer-api_pvd.json``) rather than one fictional consumer per file.
PACT_CONSUMER = "mdb_api_layer"
PACT_PROVIDER = "api_pvd"


@pytest.fixture
def pact():
    """
    Provide a fresh Pact instance per test and write the contract on teardown.

    A new Pact is created per test because once ``pact.serve()`` runs and its
    context manager exits the handle is finalized, so no further interactions
    can be added. Consumer and provider are the shared identities above; each
    test's interactions merge into the same contract file on write.

    :yields: Configured Pact instance ready for interaction definition.
        Example yield::

            Pact("mdb_api_layer", "api_pvd")
    """
    pact = Pact(PACT_CONSUMER, PACT_PROVIDER)
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

    :returns: A fresh :class:`~api.movies_api.MoviesAPI` client with its
        default TMDB ``base_url``. Example return::

            MoviesAPI()  # base_url="https://api.themoviedb.org" until repointed at the mock
    """
    return MoviesAPI()


@pytest.fixture
def pact_address():
    """Return the ``(host, port)`` the Pact mock server should bind to.

    :returns: A ``(host, port)`` tuple; port ``0`` lets the OS pick a free
        port. Example return::

            ("localhost", 0)
    """
    return PACT_MOCK_HOST, PACT_MOCK_PORT