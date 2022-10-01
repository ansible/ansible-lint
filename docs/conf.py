#
# documentation build configuration file, created by
# sphinx-quickstart on Sat Sep 27 13:23:22 2008-2009.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed
# automatically).
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.
"""Documentation Configuration."""
# pylint: disable=invalid-name
from __future__ import annotations

import os
import sys
from pathlib import Path

import pkg_resources

# Make in-tree extension importable in non-tox setups/envs, like RTD.
# Refs:
# https://github.com/readthedocs/readthedocs.org/issues/6311
# https://github.com/readthedocs/readthedocs.org/issues/7182
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# pip3 install sphinx_rtd_theme
# import sphinx_rtd_theme
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
# sys.path.append(os.path.abspath('some/directory'))
#
sys.path.insert(0, os.path.join("ansible", "lib"))
sys.path.append(os.path.abspath("_themes"))

VERSION = "latest"
AUTHOR = "Ansible, Inc"

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings.
# They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# TEST: 'sphinxcontrib.fulltoc'
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    # Third-party extensions:
    "sphinxcontrib.apidoc",
    "sphinxcontrib.programoutput",
]


# Fail safe protection to detect conflicting packages
try:
    pkg_resources.get_distribution("sphinxcontrib-programoutput")
    print(
        "FATAL: We detected presence of sphinxcontrib-programoutput package instead of sphinxcontrib-programoutput2 one. You must be sure the first is not installed.",
        file=sys.stderr,
    )
    sys.exit(2)
except pkg_resources.DistributionNotFound:
    pass

# Later on, add 'sphinx.ext.viewcode' to the list if you want to have
# colorized code generated too for references.


# Add any paths that contain templates here, relative to this directory.
templates_path = [".templates"]

# The suffix of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document.
master_doc = "index"

apidoc_excluded_paths: list[str] = []
apidoc_extra_args = [
    "--implicit-namespaces",
    "--private",  # include “_private” modules
]
apidoc_module_dir = "../src/ansiblelint"
apidoc_module_first = False
apidoc_output_dir = "pkg"
apidoc_separate_modules = True
apidoc_toc_file: str | None = None

# General substitutions.
project = "Ansible Lint Documentation"
copyright = "Ansible Lint project contributors"  # pylint: disable=redefined-builtin

github_url = "https://github.com"
github_repo_org = "ansible"
github_repo_name = "ansible-lint"
github_repo_slug = f"{github_repo_org}/{github_repo_name}"
github_repo_url = f"{github_url}/{github_repo_slug}"

extlinks = {
    "issue": (f"{github_repo_url}/issues/%s", "#"),
    "pr": (f"{github_repo_url}/pull/%s", "PR #"),
    "commit": (f"{github_repo_url}/commit/%s", ""),
    "gh": (f"{github_url}/%s", "GitHub: "),
}

intersphinx_mapping = {
    "ansible": ("https://docs.ansible.com/ansible/devel/", None),
    "ansible-core": ("https://docs.ansible.com/ansible-core/devel/", None),
    "packaging": ("https://packaging.pypa.io/en/latest", None),
    "pytest": ("https://docs.pytest.org/en/latest", None),
    "python": ("https://docs.python.org/3", None),
    "rich": ("https://rich.readthedocs.io/en/stable", None),
}

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
# The short X.Y version.
version = VERSION
# The full version, including alpha/beta/rc tags.
release = VERSION

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = "%F"  # ISO date format

# List of documents that shouldn't be included in the build.
# unused_docs = []

# List of directories, relative to source directories, that shouldn't be
# searched for source files.
# exclude_dirs = []

# A list of glob-style patterns that should be excluded when looking
# for source files.
# OBSOLETE - removing this - dharmabumstead 2018-02-06
exclude_patterns = ["README.md"]

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "any"

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "ansible"

highlight_language = "YAML+Jinja"

# Options for HTML output
# -----------------------

html_theme_path = ["../_themes"]
html_theme = "sphinx_ansible_theme"

html_theme_options = {
    "collapse_navigation": False,
    "analytics_id": "UA-128382387-1",
    # cspell:disable-next-line
    "tag_manager_id": "GTM-5FGNF6S",
    "style_nav_header_background": "#5bbdbf",
    "style_external_links": True,
    # 'canonical_url': "https://docs.ansible.com/ansible/latest/",
    "vcs_pageview_mode": "edit",
    "navigation_depth": 3,
    "display_version": False,
    "logo_only": True,
}

html_context = {
    "display_github": "True",
    "github_user": "ansible",
    "github_repo": "ansible-lint",
    "github_version": "main/docs/",
    "current_version": version,
    "latest_version": "latest",
    # list specifically out of order to make latest work
    "available_versions": ("latest",),
}

# This appears on the left side of the page, in the header bar
html_short_title = "Ansible Lint Documentation"

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
# html_style = 'solar.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = "Ansible Lint Documentation"

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
#
# ssbarnea: Do not put relative path because it will not load from some deeper
# pages as the relative path will be wrong, probably a bug in our schema.
html_logo = "_static/ansible-lint.svg"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#
# ssbarnea: Do not put SVG or PND here due to limited browser support. The
# value is relative to config file!
html_favicon = "_static/images/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['.static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = "%b %d, %Y"

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_use_modindex = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
html_copy_source = False

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
html_use_opensearch = "https://ansible-lint.readthedocs.io/"

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

autoclass_content = "both"

# table width fix via: https://rackerlabs.github.io/docs-rackspace/tools/rtd-tables.html
html_static_path = ["_static"]

html_css_files = [  # relative to html_static_path
    "theme_overrides.css",  # override wide tables in RTD theme
    "ansi.css",
]

linkcheck_workers = 25

# Matrix room links look like they have anchors
linkcheck_anchors_ignore = [
    "^!",
    "^/#[a-z]+:ansible\\.com$",
]

nitpicky = True
nitpick_ignore = [
    ("py:class", "AnsibleBaseYAMLObject"),
    ("py:class", "BasePathLike"),
    ("py:class", "CommentedMap"),
    ("py:class", "CommentedSeq"),
    ("py:class", "CompletedProcess"),
    ("py:class", "FileType"),
    ("py:class", "LintResult"),
    ("py:class", "Lintable"),
    ("py:class", "MatchError"),
    ("py:class", "Namespace"),
    ("py:class", "Path"),
    ("py:class", "Pattern"),
    ("py:class", "RulesCollection"),
    ("py:class", "StreamType"),  # used in Emitter's type annotation
    ("py:class", "Templar"),
    ("py:class", "_pytest.fixtures.SubRequest"),
    ("py:class", "ansible.parsing.yaml.objects.AnsibleBaseYAMLObject"),
    ("py:class", "ansible.template.Templar"),
    ("py:class", "handlers"),
    ("py:class", "meta"),
    ("py:class", "playbook"),
    ("py:class", "re.Pattern"),
    ("py:class", "requirements"),
    ("py:class", "role"),
    ("py:class", "ruamel.yaml.comments.CommentedMap"),
    ("py:class", "ruamel.yaml.comments.CommentedSeq"),
    ("py:class", "ruamel.yaml.constructor.RoundTripConstructor"),
    ("py:class", "ruamel.yaml.emitter.Emitter"),
    ("py:class", "ruamel.yaml.emitter.ScalarAnalysis"),
    ("py:class", "ruamel.yaml.main.YAML"),
    ("py:class", "ruamel.yaml.nodes.ScalarNode"),
    ("py:class", "ruamel.yaml.representer.RoundTripRepresenter"),
    ("py:class", "ruamel.yaml.scalarint.ScalarInt"),
    ("py:class", "ruamel.yaml.tokens.CommentToken"),
    ("py:class", "tasks"),
    ("py:class", "yaml"),
    ("py:class", "yamllint.config.YamlLintConfig"),
    ("py:obj", "Any"),
    ("py:obj", "ansiblelint.formatters.T"),
]

myst_heading_anchors = 3
myst_ref_domains = ("std", "py")
