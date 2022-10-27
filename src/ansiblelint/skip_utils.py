# (c) 2019–2020, Ansible by Red Hat
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Utils related to inline skipping of rules."""
from __future__ import annotations

import collections.abc
import logging
from functools import lru_cache
from itertools import product
from typing import TYPE_CHECKING, Any, Generator, Sequence

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
from ruamel.yaml import YAML
from ruamel.yaml.composer import ComposerError
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.tokens import CommentToken

from ansiblelint.config import used_old_tags
from ansiblelint.constants import (
    NESTED_TASK_KEYS,
    PLAYBOOK_TASK_KEYWORDS,
    RENAMED_TAGS,
    SKIPPED_RULES_KEY,
)
from ansiblelint.file_utils import Lintable

if TYPE_CHECKING:
    from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject

_logger = logging.getLogger(__name__)
_found_deprecated_tags: set[str] = set()

# playbook: Sequence currently expects only instances of one of the two
# classes below but we should consider avoiding this chimera.
# ruamel.yaml.comments.CommentedSeq
# ansible.parsing.yaml.objects.AnsibleSequence


def get_rule_skips_from_line(line: str) -> list[str]:
    """Return list of rule ids skipped via comment on the line of yaml."""
    _before_noqa, _noqa_marker, noqa_text = line.partition("# noqa")

    result = []
    for v in noqa_text.lstrip(" :").split():
        if v in RENAMED_TAGS:
            tag = RENAMED_TAGS[v]
            if v not in _found_deprecated_tags:
                _logger.warning(
                    "Replaced outdated tag '%s' with '%s', replace it to avoid future regressions",
                    v,
                    tag,
                )
                _found_deprecated_tags.add(v)
            v = tag
        result.append(v)
    return result


def append_skipped_rules(
    pyyaml_data: AnsibleBaseYAMLObject, lintable: Lintable
) -> AnsibleBaseYAMLObject:
    """Append 'skipped_rules' to individual tasks or single metadata block.

    For a file, uses 2nd parser (ruamel.yaml) to pull comments out of
    yaml subsets, check for '# noqa' skipped rules, and append any skips to the
    original parser (pyyaml) data relied on by remainder of ansible-lint.

    :param pyyaml_data: file text parsed via ansible and pyyaml.
    :param file_text: raw file text.
    :param file_type: type of file: tasks, handlers or meta.
    :returns: original pyyaml_data altered with a 'skipped_rules' list added \
              to individual tasks, or added to the single metadata block.
    """
    try:
        yaml_skip = _append_skipped_rules(pyyaml_data, lintable)
    except RuntimeError:
        # Notify user of skip error, do not stop, do not change exit code
        _logger.error("Error trying to append skipped rules", exc_info=True)
        return pyyaml_data

    if not yaml_skip:
        return pyyaml_data

    return yaml_skip


@lru_cache(maxsize=None)
def load_data(file_text: str) -> Any:
    """Parse ``file_text`` as yaml and return parsed structure.

    This is the main culprit for slow performance, each rule asks for loading yaml again and again
    ideally the ``maxsize`` on the decorator above MUST be great or equal total number of rules
    :param file_text: raw text to parse
    :return: Parsed yaml
    """
    yaml = YAML()
    # Ruamel role is not to validate the yaml file, so we ignore duplicate keys:
    yaml.allow_duplicate_keys = True
    try:
        return yaml.load(file_text)
    except ComposerError:
        # load fails on multi-documents with ComposerError exception
        return yaml.load_all(file_text)


def _append_skipped_rules(  # noqa: max-complexity: 12
    pyyaml_data: AnsibleBaseYAMLObject, lintable: Lintable
) -> AnsibleBaseYAMLObject | None:
    # parse file text using 2nd parser library
    try:
        ruamel_data = load_data(lintable.content)
    except ScannerError as exc:
        _logger.debug(
            "Ignored loading skipped rules from file %s due to: %s", lintable, exc
        )
        # For unparsable file types, we return empty skip lists
        return None
    skipped_rules = _get_rule_skips_from_yaml(ruamel_data, lintable)

    if lintable.kind in [
        "yaml",
        "requirements",
        "vars",
        "meta",
        "reno",
        "test-meta",
        "galaxy",
    ]:
        # AnsibleMapping, dict
        if hasattr(pyyaml_data, "get"):
            pyyaml_data[SKIPPED_RULES_KEY] = skipped_rules
        # AnsibleSequence, list
        elif (
            not isinstance(pyyaml_data, str)
            and isinstance(pyyaml_data, collections.abc.Sequence)
            and skipped_rules
        ):
            pyyaml_data[0][SKIPPED_RULES_KEY] = skipped_rules

        return pyyaml_data

    # create list of blocks of tasks or nested tasks
    if lintable.kind in ("tasks", "handlers"):
        ruamel_task_blocks = ruamel_data
        pyyaml_task_blocks = pyyaml_data
    elif lintable.kind == "playbook":
        try:
            pyyaml_task_blocks = _get_task_blocks_from_playbook(pyyaml_data)
            ruamel_task_blocks = _get_task_blocks_from_playbook(ruamel_data)
        except (AttributeError, TypeError):
            return pyyaml_data
    else:
        # For unsupported file types, we return empty skip lists
        return None

    # get tasks from blocks of tasks
    pyyaml_tasks = _get_tasks_from_blocks(pyyaml_task_blocks)
    ruamel_tasks = _get_tasks_from_blocks(ruamel_task_blocks)

    # append skipped_rules for each task
    for ruamel_task, pyyaml_task in zip(ruamel_tasks, pyyaml_tasks):

        # ignore empty tasks
        if not pyyaml_task and not ruamel_task:
            continue

        # AnsibleUnicode or str
        if isinstance(pyyaml_task, str):
            continue

        if pyyaml_task.get("name") != ruamel_task.get("name"):
            raise RuntimeError("Error in matching skip comment to a task")
        pyyaml_task[SKIPPED_RULES_KEY] = _get_rule_skips_from_yaml(
            ruamel_task, lintable
        )

    return pyyaml_data


def _get_task_blocks_from_playbook(playbook: Sequence[Any]) -> list[Any]:
    """Return parts of playbook that contains tasks, and nested tasks.

    :param playbook: playbook yaml from yaml parser.
    :returns: list of task dictionaries.
    """
    task_blocks = []
    for play, key in product(playbook, PLAYBOOK_TASK_KEYWORDS):
        task_blocks.extend(play.get(key, []))
    return task_blocks


def _get_tasks_from_blocks(task_blocks: Sequence[Any]) -> Generator[Any, None, None]:
    """Get list of tasks from list made of tasks and nested tasks."""
    if not task_blocks:
        return

    def get_nested_tasks(task: Any) -> Generator[Any, None, None]:
        if not task or not is_nested_task(task):
            return
        for k in NESTED_TASK_KEYS:
            if k in task and task[k]:
                if hasattr(task[k], "get"):
                    continue
                for subtask in task[k]:
                    yield from get_nested_tasks(subtask)
                    yield subtask

    for task in task_blocks:
        yield from get_nested_tasks(task)
        yield task


def _get_rule_skips_from_yaml(  # noqa: max-complexity: 12
    yaml_input: Sequence[Any], lintable: Lintable
) -> Sequence[Any]:
    """Traverse yaml for comments with rule skips and return list of rules."""
    yaml_comment_obj_strings = []

    if isinstance(yaml_input, str):
        return []

    def traverse_yaml(obj: Any) -> None:
        for _, entry in obj.ca.items.items():
            for v in entry:
                if isinstance(v, CommentToken):
                    comment_str = v.value
                    if comment_str.startswith("# noqa:"):
                        line = v.start_mark.line + 1  # ruamel line numbers start at 0
                        # column = v.start_mark.column + 1  # ruamel column numbers start at 0
                        lintable.line_skips[line].update(
                            get_rule_skips_from_line(comment_str.strip())
                        )

        yaml_comment_obj_strings.append(str(obj.ca.items))
        if isinstance(obj, dict):
            for _, val in obj.items():
                if isinstance(val, (dict, list)):
                    traverse_yaml(val)
        elif isinstance(obj, list):
            for element in obj:
                if isinstance(element, (dict, list)):
                    traverse_yaml(element)
        else:
            return

    if isinstance(yaml_input, (dict, list)):
        traverse_yaml(yaml_input)

    rule_id_list = []
    for comment_obj_str in yaml_comment_obj_strings:
        for line in comment_obj_str.split(r"\n"):
            rule_id_list.extend(get_rule_skips_from_line(line))

    return [normalize_tag(tag) for tag in rule_id_list]


def normalize_tag(tag: str) -> str:
    """Return current name of tag."""
    if tag in RENAMED_TAGS:
        used_old_tags[tag] = RENAMED_TAGS[tag]
        return RENAMED_TAGS[tag]
    return tag


def is_nested_task(task: dict[str, Any]) -> bool:
    """Check if task includes block/always/rescue."""
    # Cannot really trust the input
    if isinstance(task, str):
        return False

    for key in NESTED_TASK_KEYS:
        if task.get(key):
            return True

    return False
