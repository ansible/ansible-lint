"""Transformer implementation."""
import logging
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Set, Union, cast

from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.emitter import Emitter

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML

from .errors import MatchError
from .file_utils import Lintable
from .rules import TransformMixin
from .runner import LintResult
from .skip_utils import load_data  # TODO: move load_data out of skip_utils

__all__ = ["Transformer"]

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from ruamel.yaml.comments import LineCol

_logger = logging.getLogger(__name__)

# ruamel.yaml only preserves empty (no whitespace) blank lines
# (ie "/n/n" becomes "/n/n" but "/n  /n" becomes "/n").
# So, we need to identify whitespace-only lines to drop spaces before reading.
_whitespace_only_lines_re = re.compile(r"^ +$", re.MULTILINE)

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


class FormattedEmitter(Emitter):
    """Emitter that applies custom formatting rules when dumping YAML.

    Root-level sequences are never indented.
    All subsequent levels are indented as configured (normal ruamel.yaml behavior).

    Earlier implementations used dedent on ruamel.yaml's dumped output,
    but string magic like that had a ton of problematic edge cases.
    """

    _sequence_indent = 2
    _sequence_dash_offset = 0  # Should be _sequence_indent - 2

    # NB: mypy does not support overriding attributes with properties yet:
    #     https://github.com/python/mypy/issues/4125
    #     To silence we have to ignore[override] both the @property and the method.

    @property  # type: ignore[override]
    def best_sequence_indent(self) -> int:  # type: ignore[override]
        """Return the configured sequence_indent or 2 for root level."""
        return 2 if self.column < 2 else self._sequence_indent

    @best_sequence_indent.setter
    def best_sequence_indent(self, value: int) -> None:
        """Configure how many columns to indent each sequence item (including the '-')."""
        self._sequence_indent = value

    @property  # type: ignore[override]
    def sequence_dash_offset(self) -> int:  # type: ignore[override]
        """Return the configured sequence_dash_offset or 2 for root level."""
        return 0 if self.column < 2 else self._sequence_dash_offset

    @sequence_dash_offset.setter
    def sequence_dash_offset(self, value: int) -> None:
        """Configure how many spaces to put before each sequence item's '-'."""
        self._sequence_dash_offset = value


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

    def run(self, fmt_yaml_files: bool = True, do_transforms: bool = True) -> None:
        """Execute the fmt transforms."""
        assert (
            fmt_yaml_files or do_transforms
        ), "At least one of fmt_yaml_files or do_transforms should be True."
        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = YAML(typ="rt")

        # NB: ruamel.yaml does not have typehints, so mypy complains about everything here.

        # configure yaml dump formatting
        yaml.explicit_start = True  # type: ignore[assignment]
        yaml.explicit_end = False  # type: ignore[assignment]

        # TODO: make the width configurable
        # yaml.width defaults to 80 which wraps longer lines in tests
        yaml.width = 120  # type: ignore[assignment]

        yaml.default_flow_style = False
        yaml.compact_seq_seq = (  # dash after dash
            True  # type: ignore[assignment]
        )
        yaml.compact_seq_map = (  # key after dash
            True  # type: ignore[assignment]
        )
        # yaml.indent() obscures the purpose of these vars:
        yaml.map_indent = 2  # type: ignore[assignment]
        yaml.sequence_indent = 4 if self.indent_sequences else 2  # type: ignore[assignment]
        yaml.sequence_dash_offset = yaml.sequence_indent - 2  # type: ignore[operator]

        if self.indent_sequences:  # in the future: or other formatting options
            # For root-level sequences, FormattedEmitter overrides sequence_indent
            # and sequence_dash_offset to prevent root-level indents.
            yaml.Emitter = FormattedEmitter

        # explicit_start=True + map_indent=2 + sequence_indent=2 + sequence_dash_offset=0
        # ---
        # - name: playbook
        #   loop:
        #   - item1
        #
        # explicit_start=True + map_indent=2 + sequence_indent=4 + sequence_dash_offset=2
        # With the normal Emitter
        # ---
        #   - name: playbook
        #     loop:
        #       - item1
        #
        # explicit_start=True + map_indent=2 + sequence_indent=4 + sequence_dash_offset=2
        # With the FormattedEmitter
        # ---
        # - name: playbook
        #   loop:
        #     - item1

        for file, matches in self.matches_per_file.items():
            # matches can be empty if no LintErrors were found.
            # However, we can still fmt the yaml file
            if not ((do_transforms and matches) or fmt_yaml_files):
                continue

            try:
                data: Union[CommentedMap, CommentedSeq, str] = file.content
            except (UnicodeDecodeError, IsADirectoryError):
                # we hit a binary file (eg a jar or tar.gz) or a directory
                data = ""
                file_is_yaml = False
            else:
                # str() convinces mypy that "text/yaml" is a valid Literal.
                # Otherwise, it thinks base_kind is one of playbook, meta, tasks, ...
                file_is_yaml = str(file.base_kind) == "text/yaml"

            if file_is_yaml:
                # ruamel.yaml only preserves empty (no whitespace) blank lines.
                # So, drop spaces in whitespace-only lines. ("\n  \n" -> "\n\n")
                data = _whitespace_only_lines_re.sub("", cast(str, data))
                # load_data has an lru_cache, so using it should be cached vs using YAML().load() to reload
                data = load_data(data)

            if do_transforms:
                self._do_transforms(file, data, file_is_yaml, matches)

            if file_is_yaml:
                # YAML transforms modify data in-place. Now write it to file.
                yaml.dump(data, file.path)
            # transforms for other filetypes must handle writing it to file.

    def _do_transforms(
        self,
        file: Lintable,
        data: Union[CommentedMap, CommentedSeq, str],
        file_is_yaml: bool,
        matches: List[MatchError],
    ) -> None:
        for match in sorted(matches):
            if not isinstance(match.rule, TransformMixin):
                continue
            if file_is_yaml and not match.yaml_path:
                data = cast(Union[CommentedMap, CommentedSeq], data)
                if match.match_type == "play":
                    match.yaml_path = self._get_play_path(file, match.linenumber, data)
                elif match.task or file.kind in (
                    "tasks",
                    "handlers",
                    "playbook",
                ):
                    match.yaml_path = self._get_task_path(file, match.linenumber, data)
            match.rule.transform(match, file, data)

    @staticmethod
    def _get_play_path(
        lintable: Lintable,
        linenumber: int,  # 1-based
        ruamel_data: Union[CommentedMap, CommentedSeq],
    ) -> Sequence[Union[str, int]]:
        if lintable.kind != "playbook":
            return []
        ruamel_data = cast(CommentedSeq, ruamel_data)
        lc: "LineCol"  # lc uses 0-based counts
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
            assert isinstance(lc.line, int)
            if lc.line == linenumber_0:
                return [i_play]
            if i_play > 0 and prev_play_line < linenumber_0 < lc.line:
                return [i_play - 1]
            # The previous play check (above) can't catch the last play,
            # so, handle the last play separately.
            if (
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
    ) -> Sequence[Union[str, int]]:
        if lintable.kind in ("tasks", "handlers"):
            assert isinstance(ruamel_data, CommentedSeq)
            return self._get_task_path_in_tasks_block(linenumber, ruamel_data)
        if lintable.kind == "playbook":
            assert isinstance(ruamel_data, CommentedSeq)
            return self._get_task_path_in_playbook(linenumber, ruamel_data)
        # if lintable.kind in ['yaml', 'requirements', 'vars', 'meta', 'reno']:

        return []

    def _get_task_path_in_playbook(
        self,
        linenumber: int,  # 1-based
        ruamel_data: CommentedSeq,
    ) -> Sequence[Union[str, int]]:
        play_count = len(ruamel_data)
        for i_play, play in enumerate(ruamel_data):
            i_next_play = i_play + 1
            if play_count > i_next_play:
                next_play_line = ruamel_data[i_next_play].lc.line
            else:
                next_play_line = None

            play_keys = list(play.keys())
            for tasks_keyword in PLAYBOOK_TASK_KEYWORDS:
                if not play.get(tasks_keyword):
                    continue

                try:
                    next_keyword = play_keys[play_keys.index(tasks_keyword) + 1]
                except IndexError:
                    next_block_line = None
                else:
                    next_block_line = play.lc.data[next_keyword][0]
                # last_line_in_block is 1-based; next_*_line is 0-based
                if next_block_line is not None:
                    last_line_in_block = next_block_line
                elif next_play_line is not None:
                    last_line_in_block = next_play_line
                else:
                    last_line_in_block = None

                task_path = self._get_task_path_in_tasks_block(
                    linenumber, play[tasks_keyword], last_line_in_block
                )
                if task_path:
                    # mypy gets confused without this typehint
                    tasks_keyword_path: List[Union[int, str]] = [
                        i_play,
                        tasks_keyword,
                    ]
                    return tasks_keyword_path + list(task_path)
        # probably no tasks keywords in any of the plays
        return []

    def _get_task_path_in_tasks_block(
        self,
        linenumber: int,  # 1-based
        tasks_block: CommentedSeq,
        last_line: Optional[int] = None,  # 1-based
    ) -> Sequence[Union[str, int]]:
        task: CommentedMap
        # lc (LineCol) uses 0-based counts
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
                subtask_path = self._get_task_path_in_nested_tasks_block(
                    linenumber, task, nested_task_keys, next_task_line_0
                )
                if subtask_path:
                    # mypy gets confused without this typehint
                    task_path: List[Union[str, int]] = [i_task]
                    return task_path + list(subtask_path)

            assert isinstance(task.lc.line, int)
            if task.lc.line == linenumber_0:
                return [i_task]
            if i_task > 0 and prev_task_line < linenumber_0 < task.lc.line:
                return [i_task - 1]
            # The previous task check can't catch the last task,
            # so, handle the last task separately (also after subtask checks).
            # pylint: disable=too-many-boolean-expressions
            if (
                i_task + 1 == tasks_count
                and linenumber_0 > task.lc.line
                and (next_task_line_0 is None or linenumber_0 < next_task_line_0)
                and (last_line_0 is None or linenumber_0 <= last_line_0)
            ):
                # part of this (last) task
                return [i_task]
            prev_task_line = task.lc.line
        return []

    def _get_task_path_in_nested_tasks_block(
        self,
        linenumber: int,  # 1-based
        task: CommentedMap,
        nested_task_keys: Set[str],
        next_task_line_0: Optional[int] = None,  # 0-based
    ) -> Sequence[Union[str, int]]:
        subtask: CommentedMap
        # loop through the keys in line order
        task_keys = list(task.keys())
        task_keys_by_index = dict(enumerate(task_keys))
        for task_index, task_key in enumerate(task_keys):
            nested_task_block = task[task_key]
            if task_key not in nested_task_keys or not nested_task_block:
                continue
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
                return [task_key] + list(subtask_path)
        return []
