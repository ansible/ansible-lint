"""Utility helpers to simplify working with yaml-based data."""
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union, cast


def nested_items_path(
    data: Union[Dict[Any, Any], List[Any]],
    parent_path: Optional[List[Union[str, int]]] = None,
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

    :param data: The nested data (dicts or lists).
    :param parent_path: Do not use this param. It is used internally to recursively
                        build the yielded parent path (list of keys, indexes).

    :returns: each iteration yields the key (of the parent dict) or the index (lists)
    """
    if parent_path is None:
        parent_path = []
    convert_to_tuples_type = Callable[
        [Union[Dict[Any, Any], List[Any]]],
        Iterator[Tuple[Union[str, int], Any]],
    ]
    if isinstance(data, dict):
        # dict subclasses can override items() so don't use dict.items directly
        convert_to_tuples = cast(convert_to_tuples_type, data.__class__.items)
    elif isinstance(data, list):
        convert_to_tuples = cast(convert_to_tuples_type, enumerate)
    else:
        raise TypeError(
            f"Expected a dict or a list but got {data!r} of type '{type(data)}'"
        )
    for key, value in convert_to_tuples(data):
        yield key, value, parent_path
        if isinstance(value, (dict, list)):
            yield from nested_items_path(data=value, parent_path=parent_path + [key])
