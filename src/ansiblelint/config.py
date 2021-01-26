"""Store configuration options as a singleton."""
from argparse import Namespace

options = Namespace(
    colored=True,
    cwd=".",
    display_relative_path=True,
    exclude_paths=[],
    lintables=[],
    listrules=False,
    listtags=False,
    parseable=False,
    parseable_severity=False,
    quiet=False,
    rulesdirs=[],
    skip_list=[],
    tags=[],
    verbosity=False,
    warn_list=[],
)
