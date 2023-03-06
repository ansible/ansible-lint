"""Utilities for configuring ansible runtime environment."""
import hashlib
import os


def get_cache_dir(project_dir: str) -> str:
    """Compute cache directory to be used based on project path."""
    # we only use the basename instead of the full path in order to ensure that
    # we would use the same key regardless the location of the user home
    # directory or where the project is clones (as long the project folder uses
    # the same name).
    basename = os.path.basename(os.path.abspath(project_dir)).encode(encoding="utf-8")
    # 6 chars of entropy should be enough
    cache_key = hashlib.sha256(basename).hexdigest()[:6]
    cache_dir = (
        os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        + "/ansible-compat/"
        + cache_key
    )
    return cache_dir
