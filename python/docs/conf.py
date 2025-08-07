# -- Path setup --------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------
project = "Jentic SDKs"
copyright = "2025, Jentic"
author = "Jentic"
release = "0.9.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.mermaid",
    "sphinx_copybutton",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
add_module_names = False

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/jentic/jentic-sdks",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "use_fullscreen_button": True,
    "path_to_docs": "docs",
    "use_edit_page_button": False,
    "show_navbar_depth": 2,
    "home_page_in_toc": True,
    "show_toc_level": 2,
}
html_logo = "_static/jentic_full_white.svg"
html_static_path = ["_static"]
html_css_files = [
    "dark_only.css",
]
