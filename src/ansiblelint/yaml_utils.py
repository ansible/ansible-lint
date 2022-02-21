"""Utility helpers to simplify working with yaml-based data."""
import functools
import re
from io import StringIO
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Pattern,
    Tuple,
    Union,
    cast,
)

import ruamel.yaml.events
from ruamel.yaml.emitter import Emitter

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML
from ruamel.yaml.tokens import CommentToken

import ansiblelint.skip_utils
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.utils import get_action_tasks, normalize_task, parse_yaml_linenumbers


def iter_tasks_in_file(
    lintable: Lintable, rule_id: str
) -> Iterator[Tuple[Dict[str, Any], Dict[str, Any], bool, Optional[MatchError]]]:
    """Iterate over tasks in file.

    This yields a 4-tuple of raw_task, normalized_task, skipped, and error.

    raw_task:
        When looping through the tasks in the file, each "raw_task" is minimally
        processed to include these special keys: __line__, __file__, skipped_rules.
    normalized_task:
        When each raw_task is "normalized", action shorthand (strings) get parsed
        by ansible into python objects and the action key gets normalized. If the task
        should be skipped (skipped is True) or normalizing it fails (error is not None)
        then this is just the raw_task instead of a normalized copy.
    skipped:
        Whether or not the task should be skipped according to tags or skipped_rules.
    error:
        This is normally None. It will be a MatchError when the raw_task cannot be
        normalized due to an AnsibleParserError.

    :param lintable: The playbook or tasks/handlers yaml file to get tasks from
    :param rule_id: The current rule id to allow calculating skipped.

    :return: raw_task, normalized_task, skipped, error
    """
    data = parse_yaml_linenumbers(lintable)
    if not data:
        return
    data = ansiblelint.skip_utils.append_skipped_rules(data, lintable)

    raw_tasks = get_action_tasks(data, lintable)

    for raw_task in raw_tasks:
        err: Optional[MatchError] = None

        # An empty `tags` block causes `None` to be returned if
        # the `or []` is not present - `task.get('tags', [])`
        # does not suffice.
        skipped_in_task_tag = "skip_ansible_lint" in (raw_task.get("tags") or [])
        skipped_in_yaml_comment = rule_id in raw_task.get("skipped_rules", ())
        skipped = skipped_in_task_tag or skipped_in_yaml_comment
        if skipped:
            yield raw_task, raw_task, skipped, err
            continue

        try:
            normalized_task = normalize_task(raw_task, str(lintable.path))
        except MatchError as err:
            # normalize_task converts AnsibleParserError to MatchError
            yield raw_task, raw_task, skipped, err
            return

        yield raw_task, normalized_task, skipped, err


def nested_items_path(
    data_collection: Union[Dict[Any, Any], List[Any]],
) -> Iterator[Tuple[Any, Any, List[Union[str, int]]]]:
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

        - name: a play
          tasks:
          - name: a task
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
    yield from _nested_items_path(data_collection=data_collection, parent_path=[])


def _nested_items_path(
    data_collection: Union[Dict[Any, Any], List[Any]],
    parent_path: List[Union[str, int]],
) -> Iterator[Tuple[Any, Any, List[Union[str, int]]]]:
    """Iterate through data_collection (internal implementation of nested_items_path).

    This is a separate function because callers of nested_items_path should
    not be using the parent_path param which is used in recursive _nested_items_path
    calls to build up the path to the parent object of the current key/index, value.
    """
    # we have to cast each convert_to_tuples assignment or mypy complains
    # that both assignments (for dict and list) do not have the same type
    convert_to_tuples_type = Callable[[], Iterator[Tuple[Union[str, int], Any]]]
    if isinstance(data_collection, dict):
        convert_data_collection_to_tuples = cast(
            convert_to_tuples_type, functools.partial(data_collection.items)
        )
    elif isinstance(data_collection, list):
        convert_data_collection_to_tuples = cast(
            convert_to_tuples_type, functools.partial(enumerate, data_collection)
        )
    else:
        raise TypeError(
            f"Expected a dict or a list but got {data_collection!r} "
            f"of type '{type(data_collection)}'"
        )
    for key, value in convert_data_collection_to_tuples():
        yield key, value, parent_path
        if isinstance(value, (dict, list)):
            yield from _nested_items_path(
                data_collection=value, parent_path=parent_path + [key]
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

    _sequence_indent = 2
    _sequence_dash_offset = 0  # Should be _sequence_indent - 2
    _root_is_sequence = False

    @property
    def _is_root_level_sequence(self) -> bool:
        """Return True if this is a sequence at the root level of the yaml document."""
        return self.column < 2 and self._root_is_sequence

    def expect_node(
        self,
        root: bool = False,
        sequence: bool = False,
        mapping: bool = False,
        simple_key: bool = False,
    ) -> None:
        """Expect node (extend to record if the root doc is a sequence)."""
        if root and isinstance(self.event, ruamel.yaml.events.SequenceStartEvent):
            self._root_is_sequence = True
        return super().expect_node(root, sequence, mapping, simple_key)

    # NB: mypy does not support overriding attributes with properties yet:
    #     https://github.com/python/mypy/issues/4125
    #     To silence we have to ignore[override] both the @property and the method.

    @property  # type: ignore[override]
    def best_sequence_indent(self) -> int:  # type: ignore[override]
        """Return the configured sequence_indent or 2 for root level."""
        return 2 if self._is_root_level_sequence else self._sequence_indent

    @best_sequence_indent.setter
    def best_sequence_indent(self, value: int) -> None:
        """Configure how many columns to indent each sequence item (including the '-')."""
        self._sequence_indent = value

    @property  # type: ignore[override]
    def sequence_dash_offset(self) -> int:  # type: ignore[override]
        """Return the configured sequence_dash_offset or 2 for root level."""
        return 0 if self._is_root_level_sequence else self._sequence_dash_offset

    @sequence_dash_offset.setter
    def sequence_dash_offset(self, value: int) -> None:
        """Configure how many spaces to put before each sequence item's '-'."""
        self._sequence_dash_offset = value

    def choose_scalar_style(self) -> Any:
        """Select how to quote scalars if needed."""
        style = super().choose_scalar_style()
        if style != "'":
            # block scalar, double quoted, etc.
            return style
        if '"' in self.event.value:
            return "'"
        return self.preferred_quote

    def write_indicator(
        self,
        indicator: str,  # ruamel.yaml typehint is wrong. This is a string.
        need_whitespace: bool,
        whitespace: bool = False,
        indention: bool = False,  # (sic) ruamel.yaml has this typo in their API
    ) -> None:
        """Make sure that flow maps get whitespace by the curly braces."""
        # If this is the end of the flow mapping that isn't on a new line:
        if indicator == "}" and self.column > self.indent:
            indicator = " }"
        super(FormattedEmitter, self).write_indicator(
            indicator, need_whitespace, whitespace, indention
        )
        # if it is the start of a flow mapping, and it's not time
        # to wrap the lines, insert a space.
        if indicator == "{" and self.column < self.best_width:
            self.column += 1
            self.stream.write(" ")

    # "/n/n" results in one blank line (end the previous line, then newline).
    # So, "/n/n/n" or more is too many new lines. Clean it up.
    _re_repeat_blank_lines: Pattern = re.compile(r"\n{3,}")

    # comment is a CommentToken, not Any (Any is ruamel.yaml's lazy type hint).
    def write_comment(self, comment: CommentToken, pre: bool = False) -> None:
        """Clean up extra new lines and spaces in comments.

        ruamel.yaml treats new or empty lines as comments.
        See: https://stackoverflow.com/a/42712747/1134951
        """
        value: str = comment.value
        if (
            pre
            and not value.strip()
            and not isinstance(
                self.event,
                (
                    ruamel.yaml.events.CollectionEndEvent,
                    ruamel.yaml.events.DocumentEndEvent,
                    ruamel.yaml.events.StreamEndEvent,
                ),
            )
        ):
            # drop pure whitespace pre comments
            # does not apply to End events since they consume one of the newlines.
            value = ""
        elif pre:
            # preserve content in pre comment with at least one newline,
            # but no extra blank lines.
            value = self._re_repeat_blank_lines.sub("\n", value)
        else:
            # single blank lines in post comments
            value = self._re_repeat_blank_lines.sub("\n\n", value)
        comment.value = value

        # make sure that the comment only has one space before it.
        if comment.column > self.column + 1:
            comment.column = self.column + 1
        return super().write_comment(comment, pre)

    def write_version_directive(self, version_text: Any) -> None:
        """Skip writing '%YAML 1.1'."""
        if version_text == "1.1":
            return
        return super().write_version_directive(version_text)


class FormattedYAML(YAML):
    """A YAML loader/dumper that handles ansible content better by default."""

    def __init__(
        self,
        *,
        typ: Optional[str] = None,
        pure: bool = False,
        output: Any = None,
        # input: Any = None,
        plug_ins: Optional[List[str]] = None,
    ):
        """Return a configured ``ruamel.yaml.YAML`` instance.

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
            - name: playbook
              tasks:
              - name: task

        This example indents all sequences including the root-level:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=4
            yaml.sequence_dash_offset=2
            # yaml.Emitter defaults to ruamel.yaml.emitter.Emitter

        .. code:: yaml

            ---
              - name: playbook
                tasks:
                  - name: task

        This example indents all sequences except at the root-level:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=4
            yaml.sequence_dash_offset=2
            yaml.Emitter = FormattedEmitter  # custom Emitter prevents root-level indents

        .. code:: yaml

            ---
            - name: playbook
              tasks:
                - name: task
        """
        # Default to reading/dumping YAML 1.1 (ruamel.yaml defaults to 1.2)
        self._yaml_version = self._yaml_version_default = (1, 1)

        super().__init__(typ=typ, pure=pure, output=output, plug_ins=plug_ins)
        # TODO: make some of these dump settings configurable in ansible-lint's options:
        #       explicit_start, explicit_end, width, indent_sequences, preferred_quote
        self.explicit_start: bool = True
        self.explicit_end: bool = False
        self.width: int = 120
        indent_sequences: bool = True
        preferred_quote: str = '"'  # either ' or "

        self.default_flow_style = False
        self.compact_seq_seq = True  # dash after dash
        self.compact_seq_map = True  # key after dash

        # Do not use yaml.indent() as it obscures the purpose of these vars:
        self.map_indent = 2  # type: ignore[assignment]
        self.sequence_indent = 4 if indent_sequences else 2
        self.sequence_dash_offset = self.sequence_indent - 2

        # If someone doesn't want our FormattedEmitter, they can change it.
        self.Emitter = FormattedEmitter

        # ignore invalid preferred_quote setting
        if preferred_quote in ['"', "'"]:
            FormattedEmitter.preferred_quote = preferred_quote
        # NB: default_style affects preferred_quote as well.
        # self.default_style ∈ None (default), '', '"', "'", '|', '>'

        # TODO: preserve_quotes loads all strings as a str subclass that carries
        #       a quote attribute. Will the str subclasses cause problems in transforms?
        #       Are there any other gotchas to this?
        # This will only preserve quotes for strings read from the file.
        # anything modified by the transform will use no quotes, preferred_quote,
        # or the quote that results in the least amount of escaping.
        # self.preserve_quotes = True

        # If needed, we can use this to change null representation to be explicit
        # (see https://stackoverflow.com/a/44314840/1134951)
        # self.Representer.add_representer(
        #     type(None),
        #     lambda self, data: self.represent_scalar("tag:yaml.org,2002:null", "null"),
        # )

    @property
    def version(self) -> Union[str, Tuple[int, int]]:
        """Return the YAML version used to parse or dump.

        Ansible uses PyYAML which only supports YAML 1.1. ruamel.yaml defaults to 1.2.
        So, we have to make sure we dump yaml files using YAML 1.1.
        We can relax the version requirement once ansible uses a version of PyYAML
        that includes this PR: https://github.com/yaml/pyyaml/pull/555
        """
        return self._yaml_version

    @version.setter
    def version(self, value: Optional[Union[str, Tuple[int, int]]]):
        """Ensure that yaml version uses our default value.

        The yaml Reader updates this value based on the ``%YAML`` directive in files.
        So, if a file does not include the directive, it sets this to None.
        But, None effectively resets the parsing version to YAML 1.2 (ruamel's default).
        """
        self._yaml_version = value if value is not None else self._yaml_version_default

    def load(self, stream: str) -> Any:
        """Load YAML content from a string while avoiding known ruamel.yaml issues."""
        # TODO: maybe add support for passing a Lintable for the stream.
        if not isinstance(stream, str):
            raise NotImplementedError(f"expected a str but got {type(stream)}")
        text, preamble_comment = self._pre_process_yaml(stream)
        data = super().load(stream=text)
        if preamble_comment is not None:
            setattr(data, "preamble_comment", preamble_comment)
        return data

    def dumps(self, data: Any) -> str:
        """Dump YAML document to string (including its preamble_comment)."""
        preamble_comment: Optional[str] = getattr(data, "preamble_comment", None)
        with StringIO() as stream:
            if preamble_comment:
                stream.write(preamble_comment)
            self.dump(data, stream)
            text = stream.getvalue()
        return self._post_process_yaml(text)

    # ruamel.yaml only preserves empty (no whitespace) blank lines
    # (ie "/n/n" becomes "/n/n" but "/n  /n" becomes "/n").
    # So, we need to identify whitespace-only lines to drop spaces before reading.
    _whitespace_only_lines_re = re.compile(r"^ +$", re.MULTILINE)

    def _pre_process_yaml(self, text: str) -> Tuple[str, Optional[str]]:
        """Handle known issues with ruamel.yaml loading.

        Preserve blank lines despite extra whitespace.
        Preserve any preamble (aka header) comments before "---".

        For more on preamble comments, see: https://stackoverflow.com/a/70287507/1134951
        """
        text = self._whitespace_only_lines_re.sub("", text)

        # I investigated extending ruamel.yaml to capture preamble comments.
        #   preamble comment goes from:
        #     DocumentStartToken.comment -> DocumentStartEvent.comment
        #   Then, in the composer:
        #     once in composer.current_event
        #       composer.compose_document()
        #         discards DocumentStartEvent
        #           move DocumentStartEvent to composer.last_event
        #           node = composer.compose_node(None, None)
        #             all document nodes get composed (events get used)
        #         discard DocumentEndEvent
        #           move DocumentEndEvent to composer.last_event
        #         return node
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
            if line.lstrip().startswith("#"):
                preamble_comments.append(line)
            elif line.startswith("---"):
                break

        return text, "".join(preamble_comments) or None

    @staticmethod
    def _post_process_yaml(text: str) -> str:
        """Handle known issues with ruamel.yaml dumping.

        Make sure there's only one newline at the end of the file.
        """
        text = text.rstrip("\n") + "\n"
        return text
