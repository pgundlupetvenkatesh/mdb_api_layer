Tests Module
============

Test Data & Schema Files
------------------------
The test suite uses the following data and schema files:

* ``tests/data/movies_test_data.yaml`` - Test cases for Movies API
* ``tests/schemas/movie_schema.json`` - JSON schema for response validation

Movies Test Data
~~~~~~~~~~~~~~~~
.. literalinclude:: ../tests/data/movies_test_data.yaml
   :language: yaml
   :caption: movies_test_data.yaml

Movie Schema
~~~~~~~~~~~~
.. literalinclude:: ../tests/schemas/movie_schema.json
   :language: json
   :caption: movie_schema.json

Data
----
.. automodule:: tests.data.data_loader
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

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