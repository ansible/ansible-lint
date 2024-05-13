"""Utility helpers to simplify working with yaml-based data."""

# pylint: disable=too-many-lines
from __future__ import annotations

import functools
import logging
import os
import re
from collections.abc import Callable, Iterator, Sequence
from io import StringIO
from pathlib import Path
from re import Pattern
from typing import TYPE_CHECKING, Any, cast

import ruamel.yaml.events
from ruamel.yaml.comments import CommentedMap, CommentedSeq, Format
from ruamel.yaml.composer import ComposerError
from ruamel.yaml.constructor import RoundTripConstructor
from ruamel.yaml.emitter import Emitter, ScalarAnalysis

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scalarint import HexInt, ScalarInt
from yamllint.config import YamlLintConfig

from ansiblelint.constants import (
    ANNOTATION_KEYS,
    NESTED_TASK_KEYS,
    PLAYBOOK_TASK_KEYWORDS,
)
from ansiblelint.utils import Task

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from ruamel.yaml.comments import LineCol
    from ruamel.yaml.compat import StreamTextType
    from ruamel.yaml.nodes import ScalarNode
    from ruamel.yaml.representer import RoundTripRepresenter
    from ruamel.yaml.tokens import CommentToken

    from ansiblelint.file_utils import Lintable

_logger = logging.getLogger(__name__)


class CustomYamlLintConfig(YamlLintConfig):  # type: ignore[misc]
    """Extension of YamlLintConfig."""

    def __init__(
        self,
        content: str | None = None,
        file: str | Path | None = None,
    ) -> None:
        """Initialize config."""
        super().__init__(content, file)
        self.incompatible = ""


def deannotate(data: Any) -> Any:
    """Remove our annotations like __file__ and __line__ and return a JSON serializable object."""
    if isinstance(data, dict):
        result = data.copy()
        for key, value in data.items():
            if key in ANNOTATION_KEYS:
                del result[key]
            else:
                result[key] = deannotate(value)
        return result
    if isinstance(data, list):
        return [deannotate(item) for item in data if item not in ANNOTATION_KEYS]
    return data


def load_yamllint_config() -> CustomYamlLintConfig:
    """Load our default yamllint config and any customized override file."""
    config = CustomYamlLintConfig(file=Path(__file__).parent / "data" / ".yamllint")
    config.incompatible = ""
    # if we detect local yamllint config we use it but raise a warning
    # as this is likely to get out of sync with our internal config.
    for path in [
        ".yamllint",
        ".yamllint.yaml",
        ".yamllint.yml",
        os.getenv("YAMLLINT_CONFIG_FILE", ""),
        os.getenv("XDG_CONFIG_HOME", "~/.config") + "/yamllint/config",
    ]:
        file = Path(path).expanduser()
        if file.is_file():
            _logger.debug(
                "Loading custom %s config file, this extends our "
                "internal yamllint config.",
                file,
            )
            custom_config = CustomYamlLintConfig(file=str(file))
            custom_config.extend(config)
            config = custom_config
            break

    # Look for settings incompatible with our reformatting
    checks: list[tuple[str, str | int | bool]] = [
        (
            "comments.min-spaces-from-content",
            1,
        ),
        (
            "comments-indentation",
            False,
        ),
        (
            "braces.min-spaces-inside",
            0,
        ),
        (
            "braces.max-spaces-inside",
            1,
        ),
        (
            "octal-values.forbid-implicit-octal",
            True,
        ),
        (
            "octal-values.forbid-explicit-octal",
            True,
        ),
        # (
        #     "key-duplicates.forbid-duplicated-merge-keys", # v1.34.0+
        #     True,
        # ),
        # (
        #   "quoted-strings.quote-type", "double",
        # ),
        # (
        #   "quoted-strings.required", "only-when-needed",
        # ),
    ]
    errors = []
    for setting, expected_value in checks:
        v = config.rules
        for key in setting.split("."):
            if not isinstance(v, dict):  # pragma: no cover
                break
            if key not in v:  # pragma: no cover
                break
            v = v[key]
        if v != expected_value:
            msg = f"{setting} must be {str(expected_value).lower()}"
            errors.append(msg)
    if errors:
        nl = "\n"
        msg = f"Found incompatible custom yamllint configuration ({file}), please either remove the file or edit it to comply with:{nl}  - {(nl + '  - ').join(errors)}.{nl}{nl}Read https://ansible.readthedocs.io/projects/lint/rules/yaml/ for more details regarding why we have these requirements. Fix mode will not be available."
        config.incompatible = msg

    _logger.debug("Effective yamllint rules used: %s", config.rules)
    return config


def nested_items_path(
    data_collection: dict[Any, Any] | list[Any],
    ignored_keys: Sequence[str] = (),
) -> Iterator[tuple[Any, Any, list[str | int]]]:
    """Iterate a nested data structure, yielding key/index, value, and parent_path.

    This is a recursive function that calls itself for each nested layer of data.
    Each iteration yields:

    1. the current item's dictionary key or list index,
    2. the current item's value, and
    3. the path to the current item from the outermost data structure.

    For dicts, the yielded (1) key and (2) value are what ``dict.items()`` yields.
    For lists, the yielded (1) index and (2) value are what ``enumerate()`` yields.
    The final component, the parent path, is a list of dict keys and list indexes.
    The parent path can be helpful in providing error messages that indicate
    precisely which part of a yaml file (or other data structure) needs to be fixed.

    For example, given this playbook:

    .. code-block:: yaml

        - name: A play
          tasks:
          - name: A task
            debug:
              msg: foobar

    Here's the first and last yielded items:

    .. code-block:: python

        >>> playbook=[{"name": "a play", "tasks": [{"name": "a task", "debug": {"msg": "foobar"}}]}]
        >>> next( nested_items_path( playbook ) )
        (0, {'name': 'a play', 'tasks': [{'name': 'a task', 'debug': {'msg': 'foobar'}}]}, [])
        >>> list( nested_items_path( playbook ) )[-1]
        ('msg', 'foobar', [0, 'tasks', 0, 'debug'])

    Note that, for outermost data structure, the parent path is ``[]`` because
    you do not need to descend into any nested dicts or lists to find the indicated
    key and value.

    If a rule were designed to prohibit "foobar" debug messages, it could use the
    parent path to provide a path to the problematic ``msg``. It might use a jq-style
    path in its error message: "the error is at ``.[0].tasks[0].debug.msg``".
    Or if a utility could automatically fix issues, it could use the path to descend
    to the parent object using something like this:

    .. code-block:: python

        target = data
        for segment in parent_path:
            target = target[segment]

    :param data_collection: The nested data (dicts or lists).

    :returns: each iteration yields the key (of the parent dict) or the index (lists)
    """
    # As typing and mypy cannot effectively ensure we are called only with
    # valid data, we better ignore NoneType
    if data_collection is None:
        return
    data: dict[Any, Any] | list[Any]
    if isinstance(data_collection, Task):
        data = data_collection.normalized_task
    else:
        data = data_collection
    yield from _nested_items_path(
        data_collection=data,
        parent_path=[],
        ignored_keys=ignored_keys,
    )


def _nested_items_path(
    data_collection: dict[Any, Any] | list[Any],
    parent_path: list[str | int],
    ignored_keys: Sequence[str] = (),
) -> Iterator[tuple[Any, Any, list[str | int]]]:
    """Iterate through data_collection (internal implementation of nested_items_path).

    This is a separate function because callers of nested_items_path should
    not be using the parent_path param which is used in recursive _nested_items_path
    calls to build up the path to the parent object of the current key/index, value.
    """
    # we have to cast each convert_to_tuples assignment or mypy complains
    # that both assignments (for dict and list) do not have the same type
    convert_to_tuples_type = Callable[[], Iterator[tuple[str | int, Any]]]
    if isinstance(data_collection, dict):
        convert_data_collection_to_tuples = cast(
            convert_to_tuples_type,
            functools.partial(data_collection.items),
        )
    elif isinstance(data_collection, list):
        convert_data_collection_to_tuples = cast(
            convert_to_tuples_type,
            functools.partial(enumerate, data_collection),
        )
    else:
        msg = f"Expected a dict or a list but got {data_collection!r} of type '{type(data_collection)}'"
        raise TypeError(msg)
    for key, value in convert_data_collection_to_tuples():
        if key in (*ANNOTATION_KEYS, *ignored_keys):
            continue
        yield key, value, parent_path
        if isinstance(value, dict | list):
            yield from _nested_items_path(
                data_collection=value,
                parent_path=[*parent_path, key],
            )


def get_path_to_play(
    lintable: Lintable,
    lineno: int,  # 1-based
    ruamel_data: CommentedMap | CommentedSeq,
) -> list[str | int]:
    """Get the path to the play in the given file at the given line number."""
    if lineno < 1:
        msg = f"expected lineno >= 1, got {lineno}"
        raise ValueError(msg)
    if lintable.kind != "playbook" or not isinstance(ruamel_data, CommentedSeq):
        return []
    lc: LineCol  # lc uses 0-based counts
    # lineno is 1-based. Convert to 0-based.
    line_index = lineno - 1

    prev_play_line_index = ruamel_data.lc.line
    last_play_index = len(ruamel_data)
    for play_index, play in enumerate(ruamel_data):
        next_play_index = play_index + 1
        if last_play_index > next_play_index:
            next_play_line_index = ruamel_data[next_play_index].lc.line
        else:
            next_play_line_index = None

        lc = play.lc
        if not isinstance(lc.line, int):
            msg = f"expected lc.line to be an int, got {lc.line!r}"
            raise TypeError(msg)
        if lc.line == line_index:
            return [play_index]
        if play_index > 0 and prev_play_line_index < line_index < lc.line:
            return [play_index - 1]
        # The previous play check (above) can't catch the last play,
        # so, handle the last play separately.
        if (
            next_play_index == last_play_index
            and line_index > lc.line
            and (next_play_line_index is None or line_index < next_play_line_index)
        ):
            # part of this (last) play
            return [play_index]
        prev_play_line_index = play.lc.line
    return []


def get_path_to_task(
    lintable: Lintable,
    lineno: int,  # 1-based
    ruamel_data: CommentedMap | CommentedSeq,
) -> list[str | int]:
    """Get the path to the task in the given file at the given line number."""
    if lineno < 1:
        msg = f"expected lineno >= 1, got {lineno}"
        raise ValueError(msg)
    if lintable.kind in ("tasks", "handlers", "playbook"):
        if not isinstance(ruamel_data, CommentedSeq):
            msg = f"expected ruamel_data to be a CommentedSeq, got {ruamel_data!r}"
            raise ValueError(msg)
        if lintable.kind in ("tasks", "handlers"):
            return _get_path_to_task_in_tasks_block(lineno, ruamel_data)
        if lintable.kind == "playbook":
            return _get_path_to_task_in_playbook(lineno, ruamel_data)

    return []


def _get_path_to_task_in_playbook(
    lineno: int,  # 1-based
    ruamel_data: CommentedSeq,
) -> list[str | int]:
    """Get the path to the task in the given playbook data at the given line number."""
    last_play_index = len(ruamel_data)
    for play_index, play in enumerate(ruamel_data):
        next_play_index = play_index + 1
        if last_play_index > next_play_index:
            next_play_line_index = ruamel_data[next_play_index].lc.line
        else:
            next_play_line_index = None

        # We clearly haven't found the right spot yet if a following play starts on an earlier line.
        if next_play_line_index and lineno > next_play_line_index:
            continue

        play_keys = list(play.keys())
        for tasks_keyword in PLAYBOOK_TASK_KEYWORDS:
            if not play.get(tasks_keyword):
                continue

            try:
                next_keyword = play_keys[play_keys.index(tasks_keyword) + 1]
            except IndexError:
                next_block_line_index = None
            else:
                next_block_line_index = play.lc.data[next_keyword][0]
            # last_lineno_in_block is 1-based; next_*_line_index is 0-based
            # next_*_line_index - 1 to get line before next_*_line_index.
            # Then + 1 to make it a 1-based number.
            if next_block_line_index is not None:
                last_lineno_in_block = next_block_line_index
            elif next_play_line_index is not None:
                last_lineno_in_block = next_play_line_index
            else:
                last_lineno_in_block = None

            task_path = _get_path_to_task_in_tasks_block(
                lineno,
                play[tasks_keyword],
                last_lineno_in_block,
            )
            if task_path:
                # mypy gets confused without this typehint
                tasks_keyword_path: list[int | str] = [
                    play_index,
                    tasks_keyword,
                ]
                return tasks_keyword_path + list(task_path)
    # lineno is before first play or no tasks keywords in any of the plays
    return []


def _get_path_to_task_in_tasks_block(
    lineno: int,  # 1-based
    tasks_block: CommentedSeq,
    last_lineno: int | None = None,  # 1-based
) -> list[str | int]:
    """Get the path to the task in the given tasks block at the given line number."""
    task: CommentedMap | None
    # lineno and last_lineno are 1-based. Convert to 0-based.
    line_index = lineno - 1
    last_line_index = None if last_lineno is None else last_lineno - 1

    # lc (LineCol) uses 0-based counts
    prev_task_line_index = tasks_block.lc.line
    last_task_index = len(tasks_block)
    for task_index, task in enumerate(tasks_block):
        next_task_index = task_index + 1
        if last_task_index > next_task_index:
            if tasks_block[next_task_index] is not None:
                next_task_line_index = tasks_block[next_task_index].lc.line
            else:
                next_task_line_index = tasks_block.lc.item(next_task_index)[0]
        else:
            next_task_line_index = None

        if task is None:
            # create a dummy task to represent the null task
            task = CommentedMap()
            task.lc.line, task.lc.col = tasks_block.lc.item(task_index)

        nested_task_keys = set(task.keys()).intersection(set(NESTED_TASK_KEYS))
        if nested_task_keys:
            subtask_path = _get_path_to_task_in_nested_tasks_block(
                lineno,
                task,
                nested_task_keys,
                next_task_line_index,
            )
            if subtask_path:
                # mypy gets confused without this typehint
                task_path: list[str | int] = [task_index]
                return task_path + list(subtask_path)

        if not isinstance(task.lc.line, int):
            msg = f"expected task.lc.line to be an int, got {task.lc.line!r}"
            raise TypeError(msg)
        if task.lc.line == line_index:
            return [task_index]
        if task_index > 0 and prev_task_line_index < line_index < task.lc.line:
            return [task_index - 1]
        # The previous task check can't catch the last task,
        # so, handle the last task separately (also after subtask checks).
        # pylint: disable=too-many-boolean-expressions
        if (
            next_task_index == last_task_index
            and line_index > task.lc.line
            and (next_task_line_index is None or line_index < next_task_line_index)
            and (last_line_index is None or line_index <= last_line_index)
        ):
            # part of this (last) task
            return [task_index]
        prev_task_line_index = task.lc.line
    # line is not part of this tasks block
    return []


def _get_path_to_task_in_nested_tasks_block(
    lineno: int,  # 1-based
    task: CommentedMap,
    nested_task_keys: set[str],
    next_task_line_index: int | None = None,  # 0-based
) -> list[str | int]:
    """Get the path to the task in the given nested tasks block."""
    # loop through the keys in line order
    task_keys = list(task.keys())
    task_keys_by_index = dict(enumerate(task_keys))
    for task_index, task_key in enumerate(task_keys):
        nested_task_block = task[task_key]
        if task_key not in nested_task_keys or not nested_task_block:
            continue
        next_task_key = task_keys_by_index.get(task_index + 1, None)
        if next_task_key is not None:
            if task.lc.data[next_task_key][2] < lineno:
                continue
            next_task_key_line_index = task.lc.data[next_task_key][0]
        else:
            next_task_key_line_index = None
        # last_lineno_in_block is 1-based; next_*_line_index is 0-based
        # next_*_line_index - 1 to get line before next_*_line_index.
        # Then + 1 to make it a 1-based number.
        last_lineno_in_block = (
            next_task_key_line_index
            if next_task_key_line_index is not None
            else next_task_line_index
        )
        subtask_path = _get_path_to_task_in_tasks_block(
            lineno,
            nested_task_block,
            last_lineno_in_block,  # 1-based
        )
        if subtask_path:
            return [task_key, *list(subtask_path)]
    # line is not part of this nested tasks block
    return []


class OctalIntYAML11(ScalarInt):
    """OctalInt representation for YAML 1.1."""

    # tell mypy that ScalarInt has these attributes
    _width: Any
    _underscore: Any

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a new int with ScalarInt-defined attributes."""
        return ScalarInt.__new__(cls, *args, **kwargs)

    @staticmethod
    def represent_octal(representer: RoundTripRepresenter, data: OctalIntYAML11) -> Any:
        """Return a YAML 1.1 octal representation.

        Based on ruamel.yaml.representer.RoundTripRepresenter.represent_octal_int()
        (which only handles the YAML 1.2 octal representation).
        """
        v = format(data, "o")
        anchor = data.yaml_anchor(any=True)
        # noinspection PyProtectedMember
        return representer.insert_underscore(
            "0",
            v,
            data._underscore,  # noqa: SLF001
            anchor=anchor,
        )


class CustomConstructor(RoundTripConstructor):
    """Custom YAML constructor that preserves Octal formatting in YAML 1.1."""

    def construct_yaml_int(self, node: ScalarNode) -> Any:
        """Construct int while preserving Octal formatting in YAML 1.1.

        ruamel.yaml only preserves the octal format for YAML 1.2.
        For 1.1, it converts the octal to an int. So, we preserve the format.

        Code partially copied from ruamel.yaml (MIT licensed).
        """
        ret = super().construct_yaml_int(node)
        if self.resolver.processing_version == (1, 1) and isinstance(ret, int):
            # Do not rewrite zero as octal.
            if ret == 0:
                return ret
            # see if we've got an octal we need to preserve.
            value_su = self.construct_scalar(node)
            try:
                v = value_su.rstrip("_")
                underscore = [len(v) - v.rindex("_") - 1, False, False]  # type: Any
            except ValueError:
                underscore = None
            except IndexError:
                underscore = None
            value_s = value_su.replace("_", "")
            if value_s[0] in "+-":
                value_s = value_s[1:]
            if value_s[0:2] == "0x":
                ret = HexInt(ret, width=len(value_s) - 2)
            elif value_s[0] == "0":
                # got an octal in YAML 1.1
                ret = OctalIntYAML11(
                    ret,
                    width=None,
                    underscore=underscore,
                    anchor=node.anchor,
                )
        return ret


CustomConstructor.add_constructor(
    "tag:yaml.org,2002:int",
    CustomConstructor.construct_yaml_int,
)


class FormattedEmitter(Emitter):
    """Emitter that applies custom formatting rules when dumping YAML.

    Differences from ruamel.yaml defaults:

      - indentation of root-level sequences
      - prefer double-quoted scalars over single-quoted scalars

    This ensures that root-level sequences are never indented.
    All subsequent levels are indented as configured (normal ruamel.yaml behavior).

    Earlier implementations used dedent on ruamel.yaml's dumped output,
    but string magic like that had a ton of problematic edge cases.
    """

    preferred_quote = '"'  # either " or '

    min_spaces_inside = 0
    max_spaces_inside = 1

    _sequence_indent = 2
    _sequence_dash_offset = 0  # Should be _sequence_indent - 2
    _root_is_sequence = False

    _in_empty_flow_map = False

    @property
    def _is_root_level_sequence(self) -> bool:
        """Return True if this is a sequence at the root level of the yaml document."""
        return self.column < 2 and self._root_is_sequence

    def expect_document_root(self) -> None:
        """Expect doc root (extend to record if the root doc is a sequence)."""
        self._root_is_sequence = isinstance(
            self.event,
            ruamel.yaml.events.SequenceStartEvent,
        )
        return super().expect_document_root()

    # NB: mypy does not support overriding attributes with properties yet:
    #     https://github.com/python/mypy/issues/4125
    #     To silence we have to ignore[override] both the @property and the method.

    @property
    def best_sequence_indent(self) -> int:
        """Return the configured sequence_indent or 2 for root level."""
        return 2 if self._is_root_level_sequence else self._sequence_indent

    @best_sequence_indent.setter
    def best_sequence_indent(self, value: int) -> None:
        """Configure how many columns to indent each sequence item (including the '-')."""
        self._sequence_indent = value

    @property
    def sequence_dash_offset(self) -> int:
        """Return the configured sequence_dash_offset or 0 for root level."""
        return 0 if self._is_root_level_sequence else self._sequence_dash_offset

    @sequence_dash_offset.setter
    def sequence_dash_offset(self, value: int) -> None:
        """Configure how many spaces to put before each sequence item's '-'."""
        self._sequence_dash_offset = value

    def choose_scalar_style(self) -> Any:
        """Select how to quote scalars if needed."""
        style = super().choose_scalar_style()
        if (
            style == ""
            and self.event.value.startswith("0")
            and len(self.event.value) > 1
        ):
            if self.event.tag == "tag:yaml.org,2002:int" and self.event.implicit[0]:
                if self.event.value.startswith("0x"):
                    self.event.tag = "tag:yaml.org,2002:str"
                    return ""
                # ensures that "0123" string does not lose its quoting
                self.event.tag = "tag:yaml.org,2002:str"
                self.event.implicit = (True, True, True)
            return '"'
        if style != "'":
            # block scalar, double quoted, etc.
            return style
        if '"' in self.event.value:
            return "'"
        return self.preferred_quote

    def increase_indent(
        self,
        flow: bool = False,  # noqa: FBT002
        sequence: bool | None = None,
        indentless: bool = False,  # noqa: FBT002
    ) -> None:
        super().increase_indent(flow, sequence, indentless)
        # If our previous node was a sequence and we are still trying to indent, don't
        if self.indents.last_seq():
            self.indent = self.column + 1

    def write_indicator(
        self,
        indicator: str,  # ruamel.yaml typehint is wrong. This is a string.
        need_whitespace: bool,
        whitespace: bool = False,  # noqa: FBT002
        indention: bool = False,  # (sic) ruamel.yaml has this typo in their API # noqa: FBT002
    ) -> None:
        """Make sure that flow maps get whitespace by the curly braces."""
        # We try to go with one whitespace by the curly braces and adjust accordingly
        # to what min_spaces_inside and max_spaces_inside are set to.
        # This assumes min_spaces_inside <= max_spaces_inside
        spaces_inside = min(
            max(1, self.min_spaces_inside),
            self.max_spaces_inside if self.max_spaces_inside != -1 else 1,
        )
        # If this is the end of the flow mapping that isn't on a new line:
        if (
            indicator == "}"
            and (self.column or 0) > (self.indent or 0)
            and not self._in_empty_flow_map
        ):
            indicator = (" " * spaces_inside) + "}"
        # Indicator sometimes comes with embedded spaces we need to squish
        if indicator == "  -" and self.indents.last_seq():
            indicator = "-"
        super().write_indicator(indicator, need_whitespace, whitespace, indention)
        # if it is the start of a flow mapping, and it's not time
        # to wrap the lines, insert a space.
        if indicator == "{" and self.column < self.best_width:
            if self.check_empty_mapping():
                self._in_empty_flow_map = True
            else:
                self.column += 1
                self.stream.write(" " * spaces_inside)
                self._in_empty_flow_map = False

    # "/n/n" results in one blank line (end the previous line, then newline).
    # So, "/n/n/n" or more is too many new lines. Clean it up.
    _re_repeat_blank_lines: Pattern[str] = re.compile(r"\n{3,}")

    @staticmethod
    def add_octothorpe_protection(string: str) -> str:
        """Modify strings to protect "#" from full-line-comment post-processing."""
        try:
            if "#" in string:
                # # is \uFF03 (fullwidth number sign)
                # ﹟ is \uFE5F (small number sign)
                string = string.replace("#", "\uFF03#\uFE5F")
                # this is safe even if this sequence is present
                # because it gets reversed in post-processing
        except (ValueError, TypeError):
            # probably not really a string. Whatever.
            pass
        return string

    @staticmethod
    def drop_octothorpe_protection(string: str) -> str:
        """Remove string protection of "#" after full-line-comment post-processing."""
        try:
            if "\uFF03#\uFE5F" in string:
                # # is \uFF03 (fullwidth number sign)
                # ﹟ is \uFE5F (small number sign)
                string = string.replace("\uFF03#\uFE5F", "#")
        except (ValueError, TypeError):
            # probably not really a string. Whatever.
            pass
        return string

    def analyze_scalar(self, scalar: str) -> ScalarAnalysis:
        """Determine quoting and other requirements for string.

        And protect "#" from full-line-comment post-processing.
        """
        analysis: ScalarAnalysis = super().analyze_scalar(scalar)
        if analysis.empty:
            return analysis
        analysis.scalar = self.add_octothorpe_protection(analysis.scalar)
        return analysis

    # comment is a CommentToken, not Any (Any is ruamel.yaml's lazy type hint).
    def write_comment(
        self,
        comment: CommentToken,
        pre: bool = False,  # noqa: FBT002
    ) -> None:
        """Clean up extra new lines and spaces in comments.

        ruamel.yaml treats new or empty lines as comments.
        See: https://stackoverflow.com/questions/42708668/removing-all-blank-lines-but-not-comments-in-ruamel-yaml/42712747#42712747
        """
        value: str = comment.value
        if (
            pre
            and not value.strip()
            and not isinstance(
                self.event,
                ruamel.yaml.events.CollectionEndEvent
                | ruamel.yaml.events.DocumentEndEvent
                | ruamel.yaml.events.StreamEndEvent
                | ruamel.yaml.events.MappingStartEvent,
            )
        ):
            # drop pure whitespace pre comments
            # does not apply to End events since they consume one of the newlines.
            value = ""
        elif (
            pre
            and not value.strip()
            and isinstance(self.event, ruamel.yaml.events.MappingStartEvent)
        ):
            value = self._re_repeat_blank_lines.sub("", value)
        elif pre:
            # preserve content in pre comment with at least one newline,
            # but no extra blank lines.
            value = self._re_repeat_blank_lines.sub("\n", value)
        else:
            # single blank lines in post comments
            value = self._re_repeat_blank_lines.sub("\n\n", value)
        comment.value = value

        # make sure that the eol comment only has one space before it.
        if comment.column > self.column + 1 and not pre:
            comment.column = self.column + 1

        return super().write_comment(comment, pre)

    def write_version_directive(self, version_text: Any) -> None:
        """Skip writing '%YAML 1.1'."""
        if version_text == "1.1":
            return
        super().write_version_directive(version_text)


# pylint: disable=too-many-instance-attributes
class FormattedYAML(YAML):
    """A YAML loader/dumper that handles ansible content better by default."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        typ: str | None = None,
        pure: bool = False,
        output: Any = None,
        plug_ins: list[str] | None = None,
        version: tuple[int, int] | None = None,
    ):
        """Return a configured ``ruamel.yaml.YAML`` instance.

        Some config defaults get extracted from the yamllint config.

        ``ruamel.yaml.YAML`` uses attributes to configure how it dumps yaml files.
        Some of these settings can be confusing, so here are examples of how different
        settings will affect the dumped yaml.

        This example does not indent any sequences:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=2
            yaml.sequence_dash_offset=0

        .. code:: yaml

            ---
            - name: A playbook
              tasks:
              - name: Task

        This example indents all sequences including the root-level:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=4
            yaml.sequence_dash_offset=2
            # yaml.Emitter defaults to ruamel.yaml.emitter.Emitter

        .. code:: yaml

            ---
              - name: Playbook
                tasks:
                  - name: Task

        This example indents all sequences except at the root-level:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=4
            yaml.sequence_dash_offset=2
            yaml.Emitter = FormattedEmitter  # custom Emitter prevents root-level indents

        .. code:: yaml

            ---
            - name: Playbook
              tasks:
                - name: Task
        """
        if version:
            if isinstance(version, str):
                x, y = version.split(".", maxsplit=1)
                version = (int(x), int(y))
            self._yaml_version_default: tuple[int, int] = version
            self._yaml_version: tuple[int, int] = self._yaml_version_default
        super().__init__(typ=typ, pure=pure, output=output, plug_ins=plug_ins)

        # NB: We ignore some mypy issues because ruamel.yaml typehints are not great.

        config = self._defaults_from_yamllint_config()

        # these settings are derived from yamllint config
        self.explicit_start: bool = config["explicit_start"]  # type: ignore[assignment]
        self.explicit_end: bool = config["explicit_end"]  # type: ignore[assignment]
        self.width: int = config["width"]  # type: ignore[assignment]
        indent_sequences: bool = cast(bool, config["indent_sequences"])
        preferred_quote: str = cast(str, config["preferred_quote"])  # either ' or "

        min_spaces_inside: int = cast(int, config["min_spaces_inside"])
        max_spaces_inside: int = cast(int, config["max_spaces_inside"])

        self.default_flow_style = False
        self.compact_seq_seq = True  # type: ignore[assignment] # dash after dash
        self.compact_seq_map = True  # type: ignore[assignment] # key after dash

        # Do not use yaml.indent() as it obscures the purpose of these vars:
        self.map_indent = 2
        self.sequence_indent = 4 if indent_sequences else 2
        self.sequence_dash_offset = self.sequence_indent - 2

        # If someone doesn't want our FormattedEmitter, they can change it.
        self.Emitter = FormattedEmitter

        # ignore invalid preferred_quote setting
        if preferred_quote in ['"', "'"]:
            FormattedEmitter.preferred_quote = preferred_quote
        # NB: default_style affects preferred_quote as well.
        # self.default_style ∈ None (default), '', '"', "'", '|', '>'

        # spaces inside braces for flow mappings
        FormattedEmitter.min_spaces_inside = min_spaces_inside
        FormattedEmitter.max_spaces_inside = max_spaces_inside

        # We need a custom constructor to preserve Octal formatting in YAML 1.1
        self.Constructor = CustomConstructor
        self.Representer.add_representer(OctalIntYAML11, OctalIntYAML11.represent_octal)

        # We should preserve_quotes loads all strings as a str subclass that carries
        # a quote attribute. Will the str subclasses cause problems in transforms?
        # Are there any other gotchas to this?
        #
        # This will only preserve quotes for strings read from the file.
        # anything modified by the transform will use no quotes, preferred_quote,
        # or the quote that results in the least amount of escaping.

        # If needed, we can use this to change null representation to be explicit
        # (see https://stackoverflow.com/a/44314840/1134951)
        # self.Representer.add_representer(

    @staticmethod
    def _defaults_from_yamllint_config() -> dict[str, bool | int | str]:
        """Extract FormattedYAML-relevant settings from yamllint config if possible."""
        config = {
            "explicit_start": True,
            "explicit_end": False,
            "width": 160,
            "indent_sequences": True,
            "preferred_quote": '"',
            "min_spaces_inside": 0,
            "max_spaces_inside": 1,
        }
        for rule, rule_config in load_yamllint_config().rules.items():
            if not rule_config:
                # rule disabled
                continue

            # refactor this if ... elif ... elif ... else monstrosity using match/case (PEP 634) once python 3.10 is mandatory
            if rule == "document-start":
                config["explicit_start"] = rule_config["present"]
            elif rule == "document-end":
                config["explicit_end"] = rule_config["present"]
            elif rule == "line-length":
                config["width"] = rule_config["max"]
            elif rule == "braces":
                min_spaces_inside = rule_config["min-spaces-inside"]
                if min_spaces_inside:
                    config["min_spaces_inside"] = int(min_spaces_inside)
                max_spaces_inside = rule_config["max-spaces-inside"]
                if max_spaces_inside:
                    config["max_spaces_inside"] = int(max_spaces_inside)
            elif rule == "indentation":
                indent_sequences = rule_config["indent-sequences"]
                # one of: bool, "whatever", "consistent"
                # so, we use True for "whatever" and "consistent"
                config["indent_sequences"] = bool(indent_sequences)
            elif rule == "quoted-strings":
                quote_type = rule_config["quote-type"]
                # one of: single, double, any
                if quote_type == "single":
                    config["preferred_quote"] = "'"
                elif quote_type == "double":
                    config["preferred_quote"] = '"'

        return cast(dict[str, bool | int | str], config)

    @property
    def version(self) -> tuple[int, int] | None:
        """Return the YAML version used to parse or dump.

        Ansible uses PyYAML which only supports YAML 1.1. ruamel.yaml defaults to 1.2.
        So, we have to make sure we dump yaml files using YAML 1.1.
        We can relax the version requirement once ansible uses a version of PyYAML
        that includes this PR: https://github.com/yaml/pyyaml/pull/555
        """
        if hasattr(self, "_yaml_version"):
            return self._yaml_version
        return None

    @version.setter
    def version(self, value: tuple[int, int] | None) -> None:
        """Ensure that yaml version uses our default value.

        The yaml Reader updates this value based on the ``%YAML`` directive in files.
        So, if a file does not include the directive, it sets this to None.
        But, None effectively resets the parsing version to YAML 1.2 (ruamel's default).
        """
        if value is not None:
            self._yaml_version = value
        elif hasattr(self, "_yaml_version_default"):
            self._yaml_version = self._yaml_version_default
        # We do nothing if the object did not have a previous default version defined

    def load(self, stream: Path | StreamTextType) -> Any:
        """Load YAML content from a string while avoiding known ruamel.yaml issues."""
        if not isinstance(stream, str):
            msg = f"expected a str but got {type(stream)}"
            raise NotImplementedError(msg)
        # As ruamel drops comments for any document that is not a mapping or sequence,
        # we need to avoid using it to reformat those documents.
        # https://sourceforge.net/p/ruamel-yaml/tickets/460/

        text, preamble_comment = self._pre_process_yaml(stream)
        try:
            data = super().load(stream=text)
        except ComposerError:
            data = self.load_all(stream=text)
        except ParserError:
            data = None
            _logger.error(  # noqa: TRY400
                "Invalid yaml, verify the file contents and try again.",
            )
        if preamble_comment is not None and isinstance(
            data,
            CommentedMap | CommentedSeq,
        ):
            data.preamble_comment = preamble_comment  # type: ignore[union-attr]
        # Because data can validly also be None for empty documents, we cannot
        # really annotate the return type here, so we need to remember to
        # never save None or scalar data types when reformatting.
        return data

    def dumps(self, data: Any) -> str:
        """Dump YAML document to string (including its preamble_comment)."""
        preamble_comment: str | None = getattr(data, "preamble_comment", None)
        self._prevent_wrapping_flow_style(data)
        with StringIO() as stream:
            if preamble_comment:
                stream.write(preamble_comment)
            self.dump(data, stream)
            text = stream.getvalue()
        strip_version_directive = hasattr(self, "_yaml_version_default")
        return self._post_process_yaml(
            text,
            strip_version_directive=strip_version_directive,
        )

    def _prevent_wrapping_flow_style(self, data: Any) -> None:
        if not isinstance(data, CommentedMap | CommentedSeq):
            return
        for key, value, parent_path in nested_items_path(data):
            if not isinstance(value, CommentedMap | CommentedSeq):
                continue
            fa: Format = value.fa
            if fa.flow_style():
                predicted_indent = self._predict_indent_length(parent_path, key)
                predicted_width = len(str(value))
                if predicted_indent + predicted_width > self.width:
                    # this flow-style map will probably get line-wrapped,
                    # so, switch it to block style to avoid the line wrap.
                    fa.set_block_style()

    def _predict_indent_length(self, parent_path: list[str | int], key: Any) -> int:
        indent = 0

        # each parent_key type tells us what the indent is for the next level.
        for parent_key in parent_path:
            if isinstance(parent_key, int) and indent == 0:
                # root level is a sequence
                indent += self.sequence_dash_offset
            elif isinstance(parent_key, int):
                # next level is a sequence
                indent += cast(int, self.sequence_indent)
            elif isinstance(parent_key, str):
                # next level is a map
                indent += cast(int, self.map_indent)

        if isinstance(key, int) and indent == 0:
            # flow map is an item in a root-level sequence
            indent += self.sequence_dash_offset
        elif isinstance(key, int) and indent > 0:
            # flow map is in a sequence
            indent += cast(int, self.sequence_indent)
        elif isinstance(key, str):
            # flow map is in a map
            indent += len(key + ": ")

        return indent

    # ruamel.yaml only preserves empty (no whitespace) blank lines
    # (ie "/n/n" becomes "/n/n" but "/n  /n" becomes "/n").
    # So, we need to identify whitespace-only lines to drop spaces before reading.
    _whitespace_only_lines_re = re.compile(r"^ +$", re.MULTILINE)

    def _pre_process_yaml(self, text: str) -> tuple[str, str | None]:
        """Handle known issues with ruamel.yaml loading.

        Preserve blank lines despite extra whitespace.
        Preserve any preamble (aka header) comments before "---".

        For more on preamble comments, see: https://stackoverflow.com/questions/70286108/python-ruamel-yaml-package-how-to-get-header-comment-lines/70287507#70287507
        """
        text = self._whitespace_only_lines_re.sub("", text)

        # I investigated extending ruamel.yaml to capture preamble comments.
        #   preamble comment goes from:
        #     DocumentStartToken.comment -> DocumentStartEvent.comment
        #   Then, in the composer:
        #     once in composer.current_event
        #         discards DocumentStartEvent
        #           move DocumentStartEvent to composer.last_event
        #             all document nodes get composed (events get used)
        #         discard DocumentEndEvent
        #           move DocumentEndEvent to composer.last_event
        # So, there's no convenient way to extend the composer
        # to somehow capture the comments and pass them on.

        preamble_comments = []
        if "\n---\n" not in text and "\n--- " not in text:
            # nothing is before the document start mark,
            # so there are no comments to preserve.
            return text, None
        for line in text.splitlines(True):
            # We only need to capture the preamble comments. No need to remove them.
            # lines might also include directives.
            if line.lstrip().startswith("#") or line == "\n":
                preamble_comments.append(line)
            elif line.startswith("---"):
                break

        return text, "".join(preamble_comments) or None

    @staticmethod
    def _post_process_yaml(text: str, *, strip_version_directive: bool = False) -> str:
        """Handle known issues with ruamel.yaml dumping.

        Make sure there's only one newline at the end of the file.

        Fix the indent of full-line comments to match the indent of the next line.
        See: https://stackoverflow.com/questions/71354698/how-can-i-use-the-ruamel-yaml-rtsc-mode/71355688#71355688
        Also, removes "#" protection from strings that prevents them from being
        identified as full line comments in post-processing.

        Make sure null list items don't end in a space.
        """
        # remove YAML directive
        if strip_version_directive and text.startswith("%YAML"):
            text = text.split("\n", 1)[1]

        text = text.rstrip("\n") + "\n"

        lines = text.splitlines(keepends=True)
        full_line_comments: list[tuple[int, str]] = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:
                # blank line. Move on.
                continue

            space_length = len(line) - len(stripped)

            if stripped.startswith("#"):
                # got a full line comment

                # allow some full line comments to match the previous indent
                if i > 0 and not full_line_comments and space_length:
                    prev = lines[i - 1]
                    prev_space_length = len(prev) - len(prev.lstrip())
                    if prev_space_length == space_length:
                        # if the indent matches the previous line's indent, skip it.
                        continue

                full_line_comments.append((i, stripped))
            elif full_line_comments:
                # end of full line comments so adjust to match indent of this line
                spaces = " " * space_length
                for index, comment in full_line_comments:
                    lines[index] = spaces + comment
                full_line_comments.clear()

            cleaned = line.strip()
            if not cleaned.startswith("#") and cleaned.endswith("-"):
                # got an empty list item. drop any trailing spaces.
                lines[i] = line.rstrip() + "\n"

        text = "".join(
            FormattedEmitter.drop_octothorpe_protection(line) for line in lines
        )
        return text


def clean_json(
    obj: Any,
    func: Callable[[str], Any] = lambda key: (
        key.startswith("__") if isinstance(key, str) else False
    ),
) -> Any:
    """Remove all keys matching the condition from a nested JSON-like object.

    :param obj: a JSON like object to clean, also returned for chaining.
    :param func: a callable that takes a key in argument and return True for each key to delete
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if func(key):
                del obj[key]
            else:
                clean_json(obj[key], func)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            if func(obj[i]):
                del obj[i]
            else:
                clean_json(obj[i], func)
    else:
        # neither a dict nor a list, do nothing
        pass
    return obj
