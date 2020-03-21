try:
    from ansiblelint.rule import AnsibleLintRule  # noqa: F401
    from ansiblelint.rule import Match  # noqa: F401
    from ansiblelint.rule import RulesCollection  # noqa: F401
    from ansiblelint.rule import Runner  # noqa: F401
    from ansiblelint.rule import default_rulesdir  # noqa: F401
except ImportError:
    # Workaround for ImportError/ModuleNotFoundError errors during packaging
    # with older versions of pip/setuptools.
    pass
