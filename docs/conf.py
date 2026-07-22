import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Importing locust monkey-patches ssl via gevent, which breaks inside Sphinx
# (ssl is already imported) with a RecursionError. Docs only need the module
# importable, not patched, so skip the patching when autodoc imports
# performance.locustfile.
os.environ.setdefault("LOCUST_SKIP_MONKEY_PATCH", "1")

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'mdb_api_layer'
copyright = '2026, Pratik Gundlupet Venkatesh'
author = 'Pratik Gundlupet Venkatesh'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

# Packages that may not be installed in the doc-build environment.
# Sphinx will generate stub objects for these so imports don't fail.
autodoc_mock_imports = [
    "groq",
    "mcp",
    "pact",
    "allure",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
