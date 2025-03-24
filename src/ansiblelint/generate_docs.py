"""Utils to generate rules documentation."""

from ansiblelint.config import PROFILES
from ansiblelint.constants import RULE_DOC_URL
from ansiblelint.output import Markdown
from ansiblelint.rules import RulesCollection, TransformMixin


def rules_as_str(rules: RulesCollection) -> str:
    """Return rules as string."""
    result = ""
    for rule in rules.alphabetical():
        if issubclass(rule.__class__, TransformMixin):
            rule.tags.insert(0, "autofix")
        tag = f"{','.join(rule.tags)}" if rule.tags else ""
        result += f"- [link={RULE_DOC_URL}{rule.id}/]{rule.id}[/link] {rule.shortdesc}\n[dim]  tags:{tag}[/]"

        if rule.version_changed and rule.version_changed != "historic":
            result += f"[dim] modified:{rule.version_changed}[/]"

        result += " \n"
    return result


def profiles_as_md(*, docs_url: str = RULE_DOC_URL) -> Markdown:
    """Return markdown representation of supported profiles."""
    result = ""

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
    return Markdown(result)
