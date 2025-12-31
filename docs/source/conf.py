import sys
from pathlib import Path

sys.path.insert(0, str(Path('..', 'src').resolve()))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PySysInfo'
copyright = '2025, Mahasvan Mohan'
author = 'Mahasvan Mohan'
release = '0.0.1'

autodoc_class_signature = "separated"
add_module_names = False
# python_use_unqualified_type_names = True

autodoc_pydantic_model_show_json = False
autodoc_pydantic_settings_show_json = False


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.autodoc_pydantic',
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
