# Documentation source for Ansible Lint

Contains the source behind [docs.ansible.com/ansible-lint](https://docs.ansible.com/ansible-lint)

Contributions to documentation are welcome. To make changes, submit a pull request that changes the reStructuredText files found the in the `rst/` directory only, and the Ansible Lint team will build and push the static files.

If you wish to verify output from the markup, such as link references, you may install [sphinx](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) and the required theme, and then build the documentation locally.

The following uses `pip` to install sphinx, and the theme:

```
pip install sphinx sphinx_rtd_theme
```

Run the following to build the documentation:

```
# Within the Galaxy project tree, set your working directory to docs/docsite
$ cd docs/docsite

# Build a local copy of the static files
$ make webdocs

# Open the site in your default browser
$ xdg-open _build/html/index.html
```

If you do not want to learn the reStructuredText format, you can also [file an issue](https://github.com/ansible/ansible-lint/issues), and let us know how we can improve our documentation.
