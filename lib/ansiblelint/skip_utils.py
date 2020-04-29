# (c) 2019, Ansible by Red Hat
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
from itertools import product
import logging

import ruamel.yaml

INLINE_SKIP_FLAG = '# noqa '

_logger = logging.getLogger(__name__)


def get_rule_skips_from_line(line):
    """Return list of rule ids skipped via comment on the line of yaml."""
    rule_id_list = []
    if INLINE_SKIP_FLAG in line:
        noqa_text = line.split(INLINE_SKIP_FLAG)[1]
        rule_id_list = noqa_text.split()
    return rule_id_list


def append_skipped_rules(pyyaml_data, file_text, file_type):
    """Append 'skipped_rules' to individual tasks or single metadata block.

    For a file, uses 2nd parser (ruamel.yaml) to pull comments out of
    yaml subsets, check for '# noqa' skipped rules, and append any skips to the
    original parser (pyyaml) data relied on by remainder of ansible-lint.

    :param pyyaml_data: file text parsed via ansible and pyyaml.
    :param file_text: raw file text.
    :param file_type: type of file: tasks, handlers or meta.
    :returns: original pyyaml_data altered with a 'skipped_rules' list added
    to individual tasks, or added to the single metadata block.
    """

    try:
        yaml_skip = _append_skipped_rules(pyyaml_data, file_text, file_type)
    except RuntimeError as exc:
        # Notify user of skip error, do not stop, do not change exit code
        _logger.error('Error trying to append skipped rules: %s', exc)
        return pyyaml_data
    return yaml_skip


def _append_skipped_rules(pyyaml_data, file_text, file_type):
    # parse file text using 2nd parser library
    yaml = ruamel.yaml.YAML()
    ruamel_data = yaml.load(file_text)

    if file_type == 'meta':
        pyyaml_data[0]['skipped_rules'] = _get_rule_skips_from_yaml(ruamel_data)
        return pyyaml_data

    # create list of blocks of tasks or nested tasks
    if file_type in ('tasks', 'handlers'):
        ruamel_task_blocks = ruamel_data
        pyyaml_task_blocks = pyyaml_data
    elif file_type in ('playbook', 'pre_tasks', 'post_tasks'):
        try:
            pyyaml_task_blocks = _get_task_blocks_from_playbook(pyyaml_data)
            ruamel_task_blocks = _get_task_blocks_from_playbook(ruamel_data)
        except (AttributeError, TypeError):
            # TODO(awcrosby): running ansible-lint on any .yml file will
            # assume it is a playbook, check needs to be added higher in the
            # call stack, and can remove this except
            return pyyaml_data
    else:
        raise RuntimeError('Unexpected file type: {}'.format(file_type))

    # get tasks from blocks of tasks
    pyyaml_tasks = _get_tasks_from_blocks(pyyaml_task_blocks)
    ruamel_tasks = _get_tasks_from_blocks(ruamel_task_blocks)

    # append skipped_rules for each task
    for ruamel_task, pyyaml_task in zip(ruamel_tasks, pyyaml_tasks):
        if pyyaml_task.get('name') != ruamel_task.get('name'):
            raise RuntimeError('Error in matching skip comment to a task')
        pyyaml_task['skipped_rules'] = _get_rule_skips_from_yaml(ruamel_task)

    return pyyaml_data


def _get_task_blocks_from_playbook(playbook):
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


def _get_tasks_from_blocks(task_blocks):
    """Get list of tasks from list made of tasks and nested tasks."""
    NESTED_TASK_KEYS = [
        'block',
        'always',
        'rescue',
    ]

    def get_nested_tasks(task):
        return (
            subtask
            for k in NESTED_TASK_KEYS if k in task
            for subtask in task[k]
        )

    for task in task_blocks:
        for sub_task in get_nested_tasks(task):
            yield sub_task
        yield task


def _get_rule_skips_from_yaml(yaml_input):
    """Traverse yaml for comments with rule skips and return list of rules."""
    def traverse_yaml(obj):
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

    yaml_comment_obj_strs = []
    traverse_yaml(yaml_input)

    rule_id_list = []
    for comment_obj_str in yaml_comment_obj_strs:
        for line in comment_obj_str.split(r'\n'):
            rule_id_list.extend(get_rule_skips_from_line(line))

    return rule_id_list
