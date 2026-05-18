Tests Module
============

Contracts
---------
.. automodule:: tests.contracts.test_movie_details
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.contracts.test_popular_movies
   :members:
   :undoc-members:
   :show-inheritance:

Data
----
.. automodule:: tests.data.data_loader
   :members:
   :undoc-members:
   :show-inheritance:

* ``tests/data/test_data.yaml`` - Test cases for Movies API

.. literalinclude:: ../tests/data/test_data.yaml
   :language: yaml
   :caption: test_data.yaml

Helpers
-------

.. toctree::
   :maxdepth: 1

   helpers_failure_analyzer
   helpers_field_assertions
   helpers_response_assertions
   helpers_test_data_generators

Lists
-----
.. automodule:: tests.lists.test_update
   :members:
   :undoc-members:
   :show-inheritance:

Movie Lists
-----------
.. automodule:: tests.movie_lists.test_popular
   :members:
   :undoc-members:
   :show-inheritance:

Pacts
-----
.. literalinclude:: ../tests/pacts/test_movie_details-api_pvd.json
   :language: json
   :caption: test_movie_details-api_pvd.json

.. literalinclude:: ../tests/pacts/test_popular_movies-api_pvd.json
   :language: json
   :caption: test_popular_movies-api_pvd.json

Conftest
--------
.. automodule:: tests.conftest
   :members:
   :undoc-members:
   :show-inheritance:

Movies
------
.. automodule:: tests.movies.test_add_rating
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.movies.test_delete_rating
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.movies.test_details
   :members:
   :undoc-members:
   :show-inheritance:

People
------
.. automodule:: tests.people.test_details
   :members:
   :undoc-members:
   :show-inheritance:

Schema
~~~~~~
.. automodule:: tests.schemas.models
   :members:
   :undoc-members:
   :show-inheritance:
