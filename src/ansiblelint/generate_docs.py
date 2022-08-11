"""Utils to generate rules documentation."""
import logging
from typing import Iterable

from rich import box

# Remove this compatibility try-catch block once we drop support for rich < 10.7.0
try:
    from rich.console import group
except ImportError:
    from rich.console import render_group as group  # type: ignore

from rich.markdown import Markdown
from rich.table import Table

from ansiblelint.config import PROFILES
from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.rules import RulesCollection

DOC_HEADER = """
# Default Rules

(lint_default_rules)=

Below you can see the list of default rules Ansible Lint use to evaluate playbooks and roles:

"""

_logger = logging.getLogger(__name__)


def rules_as_str(rules: RulesCollection) -> str:
    """Return rules as string."""
    return '\n'.join([str(rule) for rule in rules.alphabetical()])


def rules_as_md(rules: RulesCollection) -> str:
    """Return md documentation for a list of rules."""
    result = DOC_HEADER

    for rule in rules.alphabetical():

        # because title == rule.id we get the desired labels for free
        # and we do not have to insert `(target_header)=`
        title = f"{rule.id}"

        if rule.help:
            if not rule.help.startswith(f"## {rule.id}"):
                raise RuntimeError(
                    f"Rule {rule.__class__} markdown help does not start with `## {rule.id}` header.\n{rule.help}"
                )
            result += f"\n\n{rule.help}"
        else:
            description = rule.description
            if rule.link:
                description += f" [more]({rule.link})"

            result += f"\n\n## {title}\n\n**{rule.shortdesc}**\n\n{description}"

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


def profiles_as_md() -> str:
    """Return markdown representation of supported profiles."""
    result = ""
    default_rules = RulesCollection([DEFAULT_RULESDIR])

    for name, profile in PROFILES.items():
        extends = ""
        if profile.get("extends", None):
            extends = (
                f" It extends [{profile['extends']}](#{profile['extends']}) profile."
            )
        result += f"## {name}\n\n{profile['description']}{extends}\n"
        for rule, rule_data in profile["rules"].items():
            for default_rule in default_rules.rules:
                if default_rule.id == rule:
                    result += f"- [{rule}](default_rules.md/#{rule})\n"
                    break
            else:
                if not rule_data:
                    raise RuntimeError(f"Rule {rule} has no data.")
                url = rule_data.get("url", None)
                if url:
                    result += f"- [{rule}]({url})*\n"
                else:
                    raise RuntimeError("All planned rules must have an 'url' entry.")
        result += "\n"
    return result


def profiles_as_rich() -> Markdown:
    """Return rich representation of supported profiles."""
    return Markdown(profiles_as_md())
