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
import logging
from functools import lru_cache
from itertools import product
from typing import TYPE_CHECKING, Any, Generator, List, Optional, Sequence

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
from ruamel.yaml import YAML  # type: ignore

from ansiblelint.config import used_old_tags
from ansiblelint.constants import RENAMED_TAGS
from ansiblelint.file_utils import Lintable

if TYPE_CHECKING:
    from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject

_logger = logging.getLogger(__name__)


# playbook: Sequence currently expects only instances of one of the two
# classes below but we should consider avoiding this chimera.
# ruamel.yaml.comments.CommentedSeq
# ansible.parsing.yaml.objects.AnsibleSequence


def get_rule_skips_from_line(line: str) -> List[str]:
    """Return list of rule ids skipped via comment on the line of yaml."""
    _before_noqa, _noqa_marker, noqa_text = line.partition("# noqa")
    noqa_text = noqa_text.lstrip(" :")
    return noqa_text.split()


def append_skipped_rules(
    pyyaml_data: "AnsibleBaseYAMLObject", lintable: Lintable
) -> "AnsibleBaseYAMLObject":
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
        _logger.error('Error trying to append skipped rules', exc_info=True)
        return pyyaml_data

    if not yaml_skip:
        return pyyaml_data

    return yaml_skip


@lru_cache(maxsize=128)
def load_data(file_text: str) -> Any:
    """Parse ``file_text`` as yaml and return parsed structure.

    This is the main culprit for slow performance, each rule asks for loading yaml again and again
    ideally the ``maxsize`` on the decorator above MUST be great or equal total number of rules
    :param file_text: raw text to parse
    :return: Parsed yaml
    """
    yaml = YAML()
    return yaml.load(file_text)


def _append_skipped_rules(
    pyyaml_data: "AnsibleBaseYAMLObject", lintable: Lintable
) -> Optional["AnsibleBaseYAMLObject"]:
    # parse file text using 2nd parser library
    ruamel_data = load_data(lintable.content)

    if lintable.kind == 'meta':
        pyyaml_data[0]['skipped_rules'] = _get_rule_skips_from_yaml(ruamel_data)
        return pyyaml_data

    # create list of blocks of tasks or nested tasks
    if lintable.kind in ('tasks', 'handlers'):
        ruamel_task_blocks = ruamel_data
        pyyaml_task_blocks = pyyaml_data
    elif lintable.kind == 'playbook':
        try:
            pyyaml_task_blocks = _get_task_blocks_from_playbook(pyyaml_data)
            ruamel_task_blocks = _get_task_blocks_from_playbook(ruamel_data)
        except (AttributeError, TypeError):
            # TODO(awcrosby): running ansible-lint on any .yml file will
            # assume it is a playbook, check needs to be added higher in the
            # call stack, and can remove this except
            return pyyaml_data
    elif lintable.kind in ['yaml', 'requirements', 'vars', 'meta', 'reno']:
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

        if pyyaml_task.get('name') != ruamel_task.get('name'):
            raise RuntimeError('Error in matching skip comment to a task')
        pyyaml_task['skipped_rules'] = _get_rule_skips_from_yaml(ruamel_task)

    return pyyaml_data


def _get_task_blocks_from_playbook(playbook: Sequence[Any]) -> List[Any]:
    """Return parts of playbook that contains tasks, and nested tasks.

    :param playbook: playbook yaml from yaml parser.
    :returns: list of task dictionaries.
    """
    PLAYBOOK_TASK_KEYWORDS = [
        'tasks',
        'pre_tasks',
        'post_tasks',
        'handlers',
    ]

    task_blocks = []
    for play, key in product(playbook, PLAYBOOK_TASK_KEYWORDS):
        task_blocks.extend(play.get(key, []))
    return task_blocks


def _get_tasks_from_blocks(task_blocks: Sequence[Any]) -> Generator[Any, None, None]:
    """Get list of tasks from list made of tasks and nested tasks."""
    NESTED_TASK_KEYS = [
        'block',
        'always',
        'rescue',
    ]

    def get_nested_tasks(task: Any) -> Generator[Any, None, None]:
        for k in NESTED_TASK_KEYS:
            if task and k in task and task[k]:
                for subtask in task[k]:
                    yield subtask

    for task in task_blocks:
        for sub_task in get_nested_tasks(task):
            yield sub_task
        yield task


def _get_rule_skips_from_yaml(yaml_input: Sequence[Any]) -> Sequence[Any]:
    """Traverse yaml for comments with rule skips and return list of rules."""
    yaml_comment_obj_strs = []

    def traverse_yaml(obj: Any) -> None:
        yaml_comment_obj_strs.append(str(obj.ca.items))
        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, (dict, list)):
                    traverse_yaml(val)
        elif isinstance(obj, list):
            for e in obj:
                if isinstance(e, (dict, list)):
                    traverse_yaml(e)
        else:
            return

    traverse_yaml(yaml_input)

    rule_id_list = []
    for comment_obj_str in yaml_comment_obj_strs:
        for line in comment_obj_str.split(r'\n'):
            rule_id_list.extend(get_rule_skips_from_line(line))

    return [normalize_tag(tag) for tag in rule_id_list]


def normalize_tag(tag: str) -> str:
    """Return current name of tag."""
    if tag in RENAMED_TAGS:
        used_old_tags[tag] = RENAMED_TAGS[tag]
        return RENAMED_TAGS[tag]
    return tag
