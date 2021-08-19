# -*- coding: utf-8 -*-
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

import os
import sys
from pathlib import Path
from typing import List

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
sys.path.insert(0, os.path.join('ansible', 'lib'))
sys.path.append(os.path.abspath('_themes'))

VERSION = '2.6'
AUTHOR = 'Ansible, Inc'


# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings.
# They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# TEST: 'sphinxcontrib.fulltoc'
extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    # Third-party extensions:
    'sphinxcontrib.apidoc',
    'sphinxcontrib.programoutput',
    # Tree-local extensions:
    'rules_table_generator_ext',  # in-tree extension
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
templates_path = ['.templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

apidoc_excluded_paths: List[str] = []
apidoc_extra_args = [
    '--implicit-namespaces',
    '--private',  # include “_private” modules
]
apidoc_module_dir = '../src/ansiblelint'
apidoc_module_first = False
apidoc_output_dir = 'pkg'
apidoc_separate_modules = True
apidoc_toc_file = None

# General substitutions.
project = 'Ansible Lint Documentation'
copyright = "2013-2021 Ansible, Inc"  # pylint: disable=redefined-builtin

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
    'ansible': ('https://docs.ansible.com/ansible/devel/', None),
    'ansible-core': ('https://docs.ansible.com/ansible-core/devel/', None),
    'packaging': ('https://packaging.rtfd.io/en/latest', None),
    'pytest': ('https://docs.pytest.org/en/latest', None),
    'python': ('https://docs.python.org/3', None),
    'python2': ('https://docs.python.org/2', None),
    'rich': ('https://rich.rtfd.io/en/latest', None),
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
today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
# unused_docs = []

# List of directories, relative to source directories, that shouldn't be
# searched for source files.
# exclude_dirs = []

# A list of glob-style patterns that should be excluded when looking
# for source files.
# OBSOLETE - removing this - dharmabumstead 2018-02-06
exclude_patterns = ['README.md']

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = 'any'

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

highlight_language = 'YAML+Jinja'

# Substitutions, variables, entities, & shortcuts for text which do not need to link to anything.
# For titles which should be a link, use the intersphinx anchors set at the index, chapter, and
# section levels, such as  qi_start_:
rst_epilog = """
.. |acapi| replace:: *Ansible Core API Guide*
.. |acrn| replace:: *Ansible Core Release Notes*
.. |ac| replace:: Ansible Core
.. |acversion| replace:: Ansible Core Version 2.1
.. |acversionshort| replace:: Ansible Core 2.1
.. |versionshortest| replace:: 2.2
.. |versiondev| replace:: 2.3
.. |pubdate| replace:: July 19, 2016
.. |rhel| replace:: Red Hat Enterprise Linux

"""


# Options for HTML output
# -----------------------

html_theme_path = ['../_themes']
html_theme = 'sphinx_ansible_theme'

html_theme_options = {
    "collapse_navigation": False,
    "analytics_id": "UA-128382387-1",
    "style_nav_header_background": "#5bbdbf",
    "style_external_links": True,
    # 'canonical_url': "https://docs.ansible.com/ansible/latest/",
    'vcs_pageview_mode': 'edit',
    "navigation_depth": 3,
}

html_context = {
    'display_github': 'True',
    'github_user': 'ansible-community',
    'github_repo': 'ansible-lint',
    'github_version': 'main/docs/',
    'current_version': version,
    'latest_version': 'latest',
    # list specifically out of order to make latest work
    'available_versions': ('latest', 'stable'),
    'css_files': (),  # overrides to the standard theme
}

html_short_title = 'Ansible Lint Documentation'

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
# html_style = 'solar.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = 'Ansible Lint Documentation'

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
# html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/ansible-lint.svg'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['.static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

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
html_use_opensearch = 'https://ansible-lint.readthedocs.io/en/latest/'

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'Poseidodoc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class
# [howto/manual]).
latex_documents = [
    ('index', 'ansible.tex', 'Ansible 2.2 Documentation', AUTHOR, 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True

autoclass_content = 'both'

# table width fix via: https://rackerlabs.github.io/docs-rackspace/tools/rtd-tables.html
html_static_path = ['_static']

html_css_files = [
    'theme_overrides.css',  # override wide tables in RTD theme
    'ansi.css',
]

linkcheck_workers = 25

nitpicky = True
nitpick_ignore = [
    ('py:class', 'ansible.parsing.yaml.objects.AnsibleBaseYAMLObject'),
    ('py:class', 'Lintable'),
    ('py:class', 'yaml'),
    ('py:class', 'role'),
    ('py:class', 'requirements'),
    ('py:class', 'handlers'),
    ('py:class', 'tasks'),
    ('py:class', 'meta'),
    ('py:class', 'playbook'),
    ('py:class', 'AnsibleBaseYAMLObject'),
    ('py:class', 'Namespace'),
    ('py:class', 'RulesCollection'),
    ('py:class', '_pytest.fixtures.SubRequest'),
    ('py:class', 'MatchError'),
    ('py:class', 'Pattern'),
    ('py:class', 'odict'),
    ('py:class', 'LintResult'),
    ('py:obj', 'Any'),
    ('py:obj', 'ansiblelint.formatters.T'),
]
