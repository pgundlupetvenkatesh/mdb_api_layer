Tests Module
============

Test Data & Schema Files
------------------------
The test suite uses the following data and schema files:

* ``tests/data/test_data.yaml`` - Test cases for Movies API
* ``tests/schemas/movie_schema.json`` - JSON schema for response validation
* ``tests/schemas/popular_movies_schema.json`` - JSON schema for popular movies response validation
* ``tests/schemas/add_delete_rating_schema.json`` - JSON schema for adding and deleting movie rating response validation

Movies Test Data
~~~~~~~~~~~~~~~~
.. literalinclude:: ../tests/data/test_data.yaml
   :language: yaml
   :caption: test_data.yaml

Movie Schema
~~~~~~~~~~~~
.. literalinclude:: ../tests/schemas/movie_schema.json
   :language: json
   :caption: movie_schema.json

Popular Movie Schema
~~~~~~~~~~~~~~~~~~~~
.. literalinclude:: ../tests/schemas/popular_movies_schema.json
   :language: json
   :caption: popular_movie_schema.json

Add Rating Schema
~~~~~~~~~~~~~~~~~~~~
.. literalinclude:: ../tests/schemas/add_delete_rating_schema.json
   :language: json
   :caption: add_delete_rating_schema.json

Contracts
---------
.. automodule:: tests.contracts.test_movie_details
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.contracts.test_popular_movies
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Data
----
.. automodule:: tests.data.data_loader
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Helpers
-------
.. automodule:: tests.helpers.response_assertions
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.helpers.field_assertions
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: tests.helpers.test_data_generators
   :no-index:
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
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Test Movies
-----------
.. automodule:: tests.test_movies
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Test People
-----------
.. automodule:: tests.people.test_details
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance: