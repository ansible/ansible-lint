"""Inject between some delims in a file."""
from __future__ import annotations

from pathlib import Path

from ansiblelint.cli import get_rules_dirs
from ansiblelint.config import Options
from ansiblelint.rules import RulesCollection, TransformMixin


def inject(original: list[str], contents: list[str]) -> list[str]:
    """Inject the contents into the original list between the delimiters.

    Args:
    ----
        original: The original list of strings.
        contents: The contents to inject.

    Returns:
    -------
        The original list with the contents injected.
    """
    start_delim = "<!---start dynamic-->\n"
    end_delim = "<!---end dynamic-->\n"

    try:
        start = original.index(start_delim)
    except ValueError as exc:
        msg = f"Could not find {start_delim} in original"
        raise ValueError(msg) from exc

    try:
        end = original.index(end_delim)
    except ValueError as exc:
        msg = f"Could not find {end_delim} in original"
        raise ValueError(msg) from exc

    return original[: start + 1] + contents + original[end:]


def load_file(file: Path) -> list[str]:
    """Load the file into a list of strings.

    Args:
    ----
        filename: The name of the file to load.

    Returns:
    -------
        A list of strings, one for each line in the file.
    """
    with file.open(encoding="utf-8") as fhandle:
        return fhandle.readlines()


def write_file(file: Path, contents: list[str]) -> None:
    """Write the contents to the file.

    Args:
    ----
        filename: The name of the file to write to.
        contents: The contents to write.
    """
    with file.open(encoding="utf-8", mode="w") as fhandle:
        fhandle.writelines(contents)


def main() -> None:
    """The main function."""
    file = Path("docs/autofix.md")
    # Load the original file.
    original = load_file(file)

    options = Options()
    options.rulesdirs = get_rules_dirs([])
    options.list_rules = True
    rules = RulesCollection(
        options.rulesdirs,
        options=options,
    )
    contents: list[str] = []
    for rule in rules.alphabetical():
        if issubclass(rule.__class__, TransformMixin):
            url = f"rules/{rule.id}.md"
            contents.append(f"- [{rule.id}]({url})\n")

    # Inject the contents.
    injected = inject(original, contents)

    # Write the injected contents to the file.
    write_file(file, injected)


if __name__ == "__main__":
    main()
