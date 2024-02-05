"""Utils to generate rules documentation."""

import logging
from collections.abc import Iterable

from rich import box
from rich.console import RenderableType, group
from rich.markdown import Markdown
from rich.table import Table

from ansiblelint.config import PROFILES
from ansiblelint.constants import RULE_DOC_URL
from ansiblelint.rules import RulesCollection, TransformMixin

DOC_HEADER = """
# Default Rules

(lint_default_rules)=

Below you can see the list of default rules Ansible Lint use to evaluate playbooks and roles:

"""

_logger = logging.getLogger(__name__)


def rules_as_str(rules: RulesCollection) -> RenderableType:
    """Return rules as string."""
    table = Table(show_header=False, header_style="title", box=box.SIMPLE)
    for rule in rules.alphabetical():
        if issubclass(rule.__class__, TransformMixin):
            rule.tags.insert(0, "autofix")
        tag = f"[dim] ({', '.join(rule.tags)})[/dim]" if rule.tags else ""
        table.add_row(
            f"[link={RULE_DOC_URL}{rule.id}/]{rule.id}[/link]",
            rule.shortdesc + tag,
        )
    return table


def rules_as_md(rules: RulesCollection) -> str:
    """Return md documentation for a list of rules."""
    result = DOC_HEADER

    for rule in rules.alphabetical():
        # because title == rule.id we get the desired labels for free
        # and we do not have to insert `(target_header)=`
        title = f"{rule.id}"

        if rule.help:
            if not rule.help.startswith(f"# {rule.id}"):  # pragma: no cover
                msg = f"Rule {rule.__class__} markdown help does not start with `# {rule.id}` header.\n{rule.help}"
                raise RuntimeError(msg)
            result += f"\n\n{rule.help}"
        else:
            description = rule.description
            if rule.link:
                description += f" [more]({rule.link})"

            result += f"\n\n## {title}\n\n**{rule.shortdesc}**\n\n{description}"

        # Safety net for preventing us from adding autofix to rules and
        # forgetting to mention it inside their documentation.
        if "autofix" in rule.tags and "autofix" not in rule.description:
            msg = f"Rule {rule.id} is invalid because it has 'autofix' tag but this ability is not documented in its description."
            raise RuntimeError(msg)

    return result


@group()
def rules_as_rich(rules: RulesCollection) -> Iterable[Table]:
    """Print documentation for a list of rules, returns empty string."""
    width = max(16, *[len(rule.id) for rule in rules])
    for rule in rules.alphabetical():
        table = Table(show_header=True, header_style="title", box=box.MINIMAL)
        table.add_column(rule.id, style="dim", width=width)
        table.add_column(Markdown(rule.shortdesc))

        description = rule.help or rule.description
        if rule.link:
            description += f" [(more)]({rule.link})"
        table.add_row("description", Markdown(description))
        if rule.version_added:
            table.add_row("version_added", rule.version_added)
        if rule.tags:
            table.add_row("tags", ", ".join(rule.tags))
        if rule.severity:
            table.add_row("severity", rule.severity)
        yield table


def profiles_as_md(*, header: bool = False, docs_url: str = RULE_DOC_URL) -> str:
    """Return markdown representation of supported profiles."""
    result = ""

    if header:
        result += """<!---
Do not manually edit, generated from generate_docs.py
-->
# Profiles

Ansible-lint profiles gradually increase the strictness of rules as your Ansible content lifecycle.

!!! note

    Rules with `*` in the suffix are not yet implemented but are documented with linked GitHub issues.

"""

    for name, profile in PROFILES.items():
        extends = ""
        if profile.get("extends", None):
            extends = (
                f" It extends [{profile['extends']}](#{profile['extends']}) profile."
            )
        result += f"## {name}\n\n{profile['description']}{extends}\n"
        for rule, rule_data in profile["rules"].items():
            if "[" in rule:
                url = f"{docs_url}{rule.split('[')[0]}/"
            else:
                url = f"{docs_url}{rule}/"
            if not rule_data:
                result += f"- [{rule}]({url})\n"
            else:
                result += f"- [{rule}]({rule_data['url']})\n"

        result += "\n"
    return result


def profiles_as_rich() -> Markdown:
    """Return rich representation of supported profiles."""
    return Markdown(profiles_as_md())
