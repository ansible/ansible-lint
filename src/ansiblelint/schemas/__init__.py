"""Module containing cached JSON schemas."""
import os
import urllib.request

from ansiblelint.config import JSON_SCHEMAS


def refresh_schemas() -> None:
    """Refresh JSON schemas by downloading latest versions."""
    for kind, url in sorted(JSON_SCHEMAS.items()):
        path = f"{os.path.relpath(os.path.dirname(__file__))}/{kind}.json"
        print(f"Refreshing {path} ...")
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
            with open(f"{path}", "r+", encoding="utf-8") as f_out:
                if f_out.read() != content:
                    f_out.seek(0)
                    f_out.write(content)
                    f_out.truncate()
