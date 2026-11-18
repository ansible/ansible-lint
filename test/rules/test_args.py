"""Tests for args rule."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import pytest

from ansiblelint.errors import MatchError
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


def test_args_module_import_restores_existing_module(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ensure args validation restores an existing module after import."""
    module_path = tmp_path / "module_with_existing_import.py"
    module_name = "tmp.module_with_existing_import"
    module_path.write_text("VALUE = 'loaded'\n", encoding="utf-8")
    existing_module = ModuleType(module_name)

    monkeypatch.setattr(
        "ansiblelint.rules.args.load_plugin",
        lambda module_name: SimpleNamespace(
            plugin_resolved_path=str(module_path),
            plugin_resolved_name=module_name,
            resolved_fqcn="tmp.module_with_existing_import",
        ),
    )
    monkeypatch.setitem(sys.modules, module_name, existing_module)

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
    assert sys.modules[module_name] is existing_module


def test_args_rule_skips_when_resolved_path_is_lint_mock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ArgsRule returns no matches for ansible-lint mock stubs."""
    from ansiblelint.constants import MOCK_MODULE_MARKER

    stub_path = tmp_path / "stub_module.py"
    stub_path.write_text(
        f"{MOCK_MODULE_MARKER}\n"
        "from ansible.module_utils.basic import AnsibleModule\n"
        "def main():\n"
        "    AnsibleModule(argument_spec=dict()).exit_json()\n",
        encoding="utf-8",
    )
    module_name = "fake_ns.fake_coll.fake_module"

    monkeypatch.setattr(
        "ansiblelint.rules.args.load_plugin",
        lambda _name: SimpleNamespace(
            plugin_resolved_path=str(stub_path),
            plugin_resolved_name=module_name,
            resolved_fqcn=module_name,
        ),
    )

    class MockTask:
        action: dict[str, Any] = {
            "__ansible_module_original__": module_name,
            "unsupported_arg": True,
        }
        raw_task: dict[str, Any] = {"args": {}}
        line = 1

        def __getitem__(self, key: str) -> object:
            return getattr(self, key)

    results = ArgsRule().matchtask(
        cast("Task", MockTask()),
        file=Lintable("test.yml", kind="tasks"),
    )
    assert results == []


def _lint_tasks(rules: RulesCollection, tmp_path: Path, tasks: str) -> list[MatchError]:
    """Lint the given tasks, as a playbook, with the args rule only."""
    rules.register(ArgsRule())
    playbook = tmp_path / "playbook.yml"
    playbook.write_text(
        f"---\n- name: Vault test\n  hosts: localhost\n  tasks:\n{tasks}",
        encoding="utf-8",
    )
    return Runner(Lintable(playbook, kind="playbook"), rules=rules).run()


def test_args_module_vault_value_does_not_skip_validation(
    empty_rule_collection: RulesCollection,
    tmp_path: Path,
) -> None:
    """An inline !vault value must not stop the rule from validating the task."""
    results = _lint_tasks(
        empty_rule_collection,
        tmp_path,
        """\
    - name: Download with a vaulted password
      ansible.builtin.get_url:
        url_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          00000000
        mode: "0644"
""",
    )
    assert [(r.tag, r.message) for r in results] == [
        ("args[module]", "missing required arguments: dest, url"),
    ]


def test_args_module_vault_value_is_not_type_checked(
    empty_rule_collection: RulesCollection,
    tmp_path: Path,
) -> None:
    """A vault value is only known once decrypted, so its type and choices are not checked."""
    results = _lint_tasks(
        empty_rule_collection,
        tmp_path,
        """\
    - name: Download with a vaulted timeout
      ansible.builtin.get_url:
        url: https://example.com/file
        dest: /tmp/file
        mode: "0644"
        timeout: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          00000000

    - name: Start a service with a vaulted state
      ansible.builtin.service:
        name: sshd
        state: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          00000000

    - name: Download without the required options
      ansible.builtin.get_url:
        mode: "0644"
""",
    )
    # the single result comes from the last task, which proves the whole file was checked
    assert [(r.tag, r.message) for r in results] == [
        ("args[module]", "missing required arguments: dest, url"),
    ]


def test_args_module_vault_value_in_list_is_not_type_checked(
    empty_rule_collection: RulesCollection,
    tmp_path: Path,
) -> None:
    """A list holding a vault or templated item is unknown until runtime, so it is not type checked."""
    results = _lint_tasks(
        empty_rule_collection,
        tmp_path,
        """\
    - name: Download with a vaulted header list
      ansible.builtin.get_url:
        url: https://example.com/file
        dest: /tmp/file
        mode: "0644"
        headers:
          - !vault |
            $ANSIBLE_VAULT;1.1;AES256
            00000000

    - name: Download with a templated header list
      ansible.builtin.get_url:
        url: https://example.com/file
        dest: /tmp/file
        mode: "0644"
        headers:
          - "{{ header }}"

    - name: Download without the required options
      ansible.builtin.get_url:
        mode: "0644"
""",
    )
    # the single result comes from the last task, which proves the whole file was checked
    assert [(r.tag, r.message) for r in results] == [
        ("args[module]", "missing required arguments: dest, url"),
    ]
