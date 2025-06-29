# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../../..")))


project = 'MemSysExplorer Application Profilers'
copyright = '2025, Duc Nguyen, Mark Hempstead, Lillian Pentecost, Olivia Fann, TaniaPerehinets'
author = 'Duc Nguyen, Mark Hempstead, Lillian Pentecost, Olivia Fann, TaniaPerehinets'
release = '1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.viewcode', 'sphinx_autodoc_typehints', 'sphinx.ext.autosummary']

try:
    import sphinx_rtd_theme
except ImportError:
    print("Sphinx dependencies missing. Installing...")
    os.system('pip install -r ../../docs/requirements.txt')

# Options for autodoc
autodoc_default_options = {
    'members': True,           # Document class/methods
    'undoc-members': True,     # Include members without docstrings
    'private-members': True,   # Include members starting with _
    'show-inheritance': True,   # Show class inheritance
    'special-members': True
}

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_mock_imports = ["ncu_report", "sniper_lib", "pandas", "sniper_stats", "snipermem"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Add custom stylesheet
html_css_files = [
    'custom.css',
]
