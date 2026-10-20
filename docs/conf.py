from datetime import datetime
from importlib.metadata import version as distribution_version

project = "bibliography-io"
author = "Gerit Wagner"
copyright = f"{datetime.now().year}, {author}"
release = distribution_version("bibliography-io")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
html_static_path = ["_static"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_member_order = "bysource"
autodoc_typehints = "description"

html_theme = "sphinx_rtd_theme"
html_title = "bibliography-io documentation"
html_baseurl = "https://colrev-environment.github.io/bibliography-io/"
html_logo = "_static/bibliography_io_logo.png"
html_favicon = "_static/favicon.ico"
