"""Tests for args rule."""

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import pytest

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.args import ArgsRule
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from ansiblelint.utils import Task


def test_args_module_relative_import(default_rules_collection: RulesCollection) -> None:
    """Validate args check of a module with a relative import."""
    lintable = Lintable(
        "examples/playbooks/module_relative_import.yml",
        kind="playbook",
    )
    result = Runner(lintable, rules=default_rules_collection).run()
    assert len(result) == 1, result
    assert result[0].lineno in [5, 7]
    assert result[0].filename == "examples/playbooks/module_relative_import.yml"
    assert result[0].tag == "args[module]"
    assert result[0].message == "missing required arguments: name"


def test_args_module_import_keeps_module_registered(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ensure args validation preserves import semantics for module execution."""
    module_path = tmp_path / "module_with_import_time_assert.py"
    module_name = "tmp.module_with_import_time_assert"
    module_path.write_text(
        "import sys\n"
        "if sys.modules.get(__name__) is None:\n"
        "    raise RuntimeError('module not registered during import')\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "ansiblelint.rules.args.load_plugin",
        lambda module_name: SimpleNamespace(
            plugin_resolved_path=str(module_path),
            plugin_resolved_name=module_name,
            resolved_fqcn="tmp.module_with_import_time_assert",
        ),
    )
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    class MockTask:
        action: dict[str, Any] = {"__ansible_module_original__": module_name}
        raw_task: dict[str, Any] = {"args": {}}
        line = 1

        def __getitem__(self, key: str) -> object:
            return getattr(self, key)

    results = ArgsRule().matchtask(
        cast("Task", MockTask()),
        file=Lintable("test.yml", kind="tasks"),
    )

    assert results == []
    assert module_name not in sys.modules
