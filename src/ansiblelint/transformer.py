"""Transformer implementation."""
import logging
import re
from textwrap import dedent
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Union

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from ruamel.yaml.comments import LineCol

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
from ruamel.yaml import YAML  # type: ignore
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .errors import MatchError
from .file_utils import Lintable
from .rules import TransformMixin
from .runner import LintResult
from .skip_utils import load_data  # TODO: move load_data out of skip_utils

_logger = logging.getLogger(__name__)

_comment_line_re = re.compile(r"^ *#")

PLAYBOOK_TASK_KEYWORDS = [
    'tasks',
    'pre_tasks',
    'post_tasks',
    'handlers',
]
NESTED_TASK_KEYS = [
    'block',
    'always',
    'rescue',
]


# Transformer is for transforms like runner is for rules
class Transformer:
    """Transformer class performs the fmt transformations."""

    def __init__(self, result: LintResult):
        """Initialize a Transformer instance."""
        # TODO: options for explict_start, indent_sequences
        self.explicit_start = True
        self.indent_sequences = True

        self.matches: List[MatchError] = result.matches
        self.files: Set[Lintable] = result.files

        file: Lintable
        lintables: Dict[str, Lintable] = {file.filename: file for file in result.files}
        self.matches_per_file: Dict[Lintable, List[MatchError]] = {
            file: [] for file in result.files
        }

        for match in self.matches:
            try:
                lintable = lintables[match.filename]
            except KeyError:
                # we shouldn't get here, but this is easy to recover from so do that.
                lintable = Lintable(match.filename)
                self.matches_per_file[lintable] = []
            self.matches_per_file[lintable].append(match)

    def run(self, fmt_all_files=True) -> None:
        """Execute the fmt transforms."""
        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = YAML(typ="rt")

        # configure yaml dump formatting
        yaml.explicit_start = (
            False  # explicit_start is handled in self._final_yaml_transform()
        )
        yaml.explicit_end = False
        # TODO: make the width configurable
        yaml.width = 120  # defaults to 80 which wraps longer lines in tests
        yaml.default_flow_style = False
        yaml.compact_seq_seq = True  # dash after dash
        yaml.compact_seq_map = True  # key after dash
        # yaml.indent() obscures the purpose of these vars:
        yaml.map_indent = 2
        yaml.sequence_indent = 4 if self.indent_sequences else 2
        yaml.sequence_dash_offset = yaml.sequence_indent - 2

        # explicit_start=True + map_indent=2 + sequence_indent=2 + sequence_dash_offset=0
        # ---
        # - name: playbook
        #   loop:
        #   - item1
        #
        # explicit_start=True + map_indent=2 + sequence_indent=4 + sequence_dash_offset=2
        # ---
        #   - name: playbook
        #     loop:
        #       - item1

        for file, matches in self.matches_per_file.items():
            # matches can be empty if no LintErrors were found.
            # However, we can still fmt the yaml file
            if not fmt_all_files and not matches:
                continue

            data: str = file.content
            if file.base_kind == "text/yaml":
                # load_data has an lru_cache, so using it should be cached vs using YAML().load() to reload
                data: Union[CommentedMap, CommentedSeq] = load_data(data)

            for match in sorted(matches):
                if not isinstance(match.rule, TransformMixin):
                    continue
                if file.base_kind == "text/yaml" and not match.yaml_path:
                    if match.match_type == "play":
                        match.yaml_path = self._get_play_path(
                            file, match.linenumber, data
                        )
                    elif match.task or file.kind in ("tasks", "handlers", "playbook"):
                        match.yaml_path = self._get_task_path(
                            file, match.linenumber, data
                        )
                match.rule.transform(match, file, data)

            if file.base_kind == "text/yaml":
                # YAML transforms modify data in-place. Now write it to file.
                yaml.dump(data, file.path, transform=self._final_yaml_transform)
            # transforms for other filetypes must handle writing it to file.

    def _get_play_path(
        self,
        lintable: Lintable,
        linenumber: int,  # 1-based
        ruamel_data: Union[CommentedMap, CommentedSeq],
    ) -> List[Union[str, int]]:
        if lintable.kind == "playbook":
            ruamel_data: CommentedSeq
            lc: LineCol  # lc uses 0-based counts
            # linenumber and last_line are 1-based. Convert to 0-based.
            linenumber_0 = linenumber - 1

            prev_play_line = ruamel_data.lc.line
            play_count = len(ruamel_data)
            for i_play, play in enumerate(ruamel_data):
                i_next_play = i_play + 1
                if play_count > i_next_play:
                    next_play_line = ruamel_data[i_next_play].lc.line
                else:
                    next_play_line = None

                lc = play.lc
                if lc.line == linenumber_0:
                    return [i_play]
                elif i_play > 0 and prev_play_line < linenumber_0 < lc.line:
                    return [i_play - 1]
                # The previous play check (above) can't catch the last play,
                # so, handle the last play separately.
                elif (
                    i_play + 1 == play_count
                    and linenumber_0 > lc.line
                    and (next_play_line is None or linenumber_0 < next_play_line)
                ):
                    # part of this (last) play
                    return [i_play]
                prev_play_line = play.lc.line
        return []

    def _get_task_path(
        self,
        lintable: Lintable,
        linenumber: int,  # 1-based
        ruamel_data: Union[CommentedMap, CommentedSeq],
    ) -> List[Union[str, int]]:
        if lintable.kind in ("tasks", "handlers"):
            return self._get_task_path_in_tasks_block(linenumber, ruamel_data)
        elif lintable.kind == "playbook":
            return self._get_task_path_in_playbook(linenumber, ruamel_data)
        # elif lintable.kind in ['yaml', 'requirements', 'vars', 'meta', 'reno']:

        return []

    def _get_task_path_in_playbook(
        self,
        linenumber: int,  # 1-based
        ruamel_data: Union[CommentedMap, CommentedSeq],
    ) -> List[Union[str, int]]:
        ruamel_data: CommentedSeq
        play_count = len(ruamel_data)
        for i_play, play in enumerate(ruamel_data):
            i_next_play = i_play + 1
            if play_count > i_next_play:
                next_play_line = ruamel_data[i_next_play].lc.line
            else:
                next_play_line = None

            play_keys = list(play.keys())
            play_keys_by_index = dict(enumerate(play_keys))
            for tasks_keyword in PLAYBOOK_TASK_KEYWORDS:
                tasks_block = play.get(tasks_keyword, [])
                if not tasks_block:
                    continue

                play_index = play_keys.index(tasks_keyword)
                next_keyword = play_keys_by_index.get(play_index + 1, None)
                if next_keyword is not None:
                    next_block_line = play.lc.data[next_keyword][0]
                else:
                    next_block_line = None
                # last_line_in_block is 1-based; next_*_line is 0-based
                if next_block_line is not None:
                    last_line_in_block = next_block_line
                elif next_play_line is not None:
                    last_line_in_block = next_play_line
                else:
                    last_line_in_block = None

                tasks_yaml_path = self._get_task_path_in_tasks_block(
                    linenumber, tasks_block, last_line_in_block
                )
                if tasks_yaml_path:
                    return [i_play, tasks_keyword] + tasks_yaml_path

    def _get_task_path_in_tasks_block(
        self,
        linenumber: int,  # 1-based
        tasks_block: CommentedSeq,
        last_line: Optional[int] = None,  # 1-based
    ) -> List[Union[str, int]]:
        task: CommentedMap
        subtask: CommentedMap
        lc: LineCol  # lc uses 0-based counts
        # linenumber and last_line are 1-based. Convert to 0-based.
        linenumber_0 = linenumber - 1
        last_line_0 = None if last_line is None else last_line - 1

        prev_task_line = tasks_block.lc.line
        tasks_count = len(tasks_block)
        for i_task, task in enumerate(tasks_block):
            i_next_task = i_task + 1
            if tasks_count > i_next_task:
                next_task_line_0 = tasks_block[i_next_task].lc.line
            else:
                next_task_line_0 = None

            nested_task_keys = set(task.keys()).intersection(set(NESTED_TASK_KEYS))
            if nested_task_keys:
                # loop through the keys in line order
                task_keys = list(task.keys())
                task_keys_by_index = dict(enumerate(task_keys))
                for task_key in task_keys:
                    nested_task_block = task[task_key]
                    if task_key not in nested_task_keys or not nested_task_block:
                        continue
                    task_index = task_keys.index(task_key)
                    next_task_key = task_keys_by_index.get(task_index + 1, None)
                    if next_task_key is not None:
                        next_task_key_line_0 = task.lc.data[next_task_key][0]
                    else:
                        next_task_key_line_0 = None
                    # 0-based next_line - 1 to get line before next_line.
                    # Then + 1 to make it a 1-based number.
                    # So, next_task*_0 - 1 + 1 = last_block_line
                    last_block_line = (
                        next_task_key_line_0
                        if next_task_key_line_0 is not None
                        else next_task_line_0
                    )
                    subtask_path = self._get_task_path_in_tasks_block(
                        linenumber,
                        nested_task_block,
                        last_block_line,  # 1-based
                    )
                    if subtask_path:
                        return [i_task, task_key] + subtask_path

            lc = task.lc
            if lc.line == linenumber_0:
                return [i_task]
            elif i_task > 0 and prev_task_line < linenumber_0 < lc.line:
                return [i_task - 1]
            # The previous task check can't catch the last task,
            # so, handle the last task separately (also after subtask checks).
            elif (
                i_task + 1 == tasks_count
                and linenumber_0 > lc.line
                and (next_task_line_0 is None or linenumber_0 < next_task_line_0)
                and (last_line_0 is None or linenumber_0 <= last_line_0)
            ):
                # part of this (last) task
                return [i_task]
            prev_task_line = task.lc.line
        return []

    def _final_yaml_transform(self, text: str) -> str:
        """
        Ensure that top-level sequences are not over-indented.

        In order to make that work, we cannot delegate adding the yaml explict_start
        to ruamel.yaml or dedent() won't have anything to work with.
        Instead, we add the explicit_start here.
        """
        text_lines = text.splitlines(keepends=True)
        # dedent() does not handle cases where there is a comment at column 0
        text_without_comments = "".join(
            ["\n" if _comment_line_re.match(line) else line for line in text_lines]
        )
        dedented_lines = dedent(text_without_comments).splitlines(keepends=True)

        # preserve the indents for comment lines (do not dedent them)
        for i, line in enumerate(text_lines):
            if _comment_line_re.match(line):
                dedented_lines[i] = line

        text = "".join(dedented_lines)
        if self.explicit_start:
            text = "---\n" + text
        return text
