"""Tests related to use of inline noqa."""

# cspell: ignore omap
from pathlib import Path

import pytest

from ansiblelint.constants import RC, SKIPPED_RULES_KEY
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.skip_utils import append_skipped_rules
from ansiblelint.testing import run_ansible_lint


def test_role_tasks_with_block(default_rules_collection: RulesCollection) -> None:
    """Check that blocks in role tasks can contain skips."""
    results = Runner(
        "examples/playbooks/roles/fixture_1",
        rules=default_rules_collection,
    ).run()
    assert len(results) == 4
    for result in results:
        assert result.tag == "latest[git]"


@pytest.mark.parametrize(
    ("lintable", "expected"),
    (pytest.param("examples/playbooks/test_skip_inside_yaml.yml", 4, id="yaml"),),
)
def test_inline_skips(
    default_rules_collection: RulesCollection,
    lintable: str,
    expected: int,
) -> None:
    """Check that playbooks can contain skips."""
    results = Runner(lintable, rules=default_rules_collection).run()

    assert len(results) == expected


def test_role_meta() -> None:
    """Test running from inside meta folder."""
    role_path = "examples/roles/meta_noqa"

    result = run_ansible_lint("-v", role_path)
    assert len(result.stdout) == 0
    assert result.returncode == 0


def test_vars_block_scalar_noqa_4596(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
) -> None:
    """Ensure block scalar noqa ignores jinja[spacing] without silencing other lines."""
    vars_file = tmp_path / "roles" / "test_role" / "vars" / "main.yml"
    vars_file.parent.mkdir(parents=True)

    vars_file.write_text(
        "---\n"
        "some_var: >- # noqa: jinja[spacing] var-naming[no-role-prefix]\n"
        "  {{foo}}\n",
        encoding="utf-8",
    )
    assert Runner(vars_file, rules=default_rules_collection).run() == []

    vars_file.write_text(
        "---\n"
        "some_var: >- # noqa: jinja[spacing] var-naming[no-role-prefix]\n"
        "  {{foo}}\n"
        "test_role_unignored: >-\n"
        "  {{bar}}\n",
        encoding="utf-8",
    )
    matches = Runner(vars_file, rules=default_rules_collection).run()
    assert len(matches) == 1
    assert matches[0].tag == "jinja[spacing]"
    assert matches[0].lineno == 4


@pytest.mark.parametrize(
    "content",
    (
        pytest.param(
            "---\ntest_role_var: | # noqa: jinja[spacing]\n  {{foo}}\n",
            id="pipe",
        ),
        pytest.param(
            "---\ntest_role_var: |- # noqa: jinja[spacing]\n  {{foo}}\n",
            id="pipe_strip",
        ),
        pytest.param(
            "---\ntest_role_var: >+ # noqa: jinja[spacing]\n  {{foo}}\n",
            id="fold_keep",
        ),
        pytest.param(
            "---\ntest_role_var:\n  >- # noqa: jinja[spacing]\n    {{foo}}\n",
            id="next_line_indicator",
        ),
        pytest.param(
            "---\ntest_role_list:\n  - >- # noqa: jinja[spacing]\n    {{foo}}\n",
            id="sequence_item",
        ),
    ),
)
def test_vars_block_scalar_noqa_shapes(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
    content: str,
) -> None:
    """Ensure all block scalar indicator shapes honor inline noqa."""
    vars_file = tmp_path / "roles" / "test_role" / "vars" / "main.yml"
    vars_file.parent.mkdir(parents=True)
    vars_file.write_text(content, encoding="utf-8")

    matches = Runner(vars_file, rules=default_rules_collection).run()
    assert matches == []


def test_playbook_task_block_scalar_noqa(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
) -> None:
    """Ensure block scalar noqa skips both task-level and line-level rules."""
    playbook = tmp_path / "playbook.yml"
    template = (
        "---\n"
        "- name: Test block scalar noqa in task\n"
        "  hosts: localhost\n"
        "  tasks:\n"
        "    - name: Run shell command\n"
        "      changed_when: false\n"
        "      ansible.builtin.shell:\n"
        "        cmd: |-{comment}\n"
        '          echo "{{{{foo}}}}"\n'
    )

    playbook.write_text(template.format(comment=""), encoding="utf-8")
    unignored_tags = {
        match.tag for match in Runner(playbook, rules=default_rules_collection).run()
    }
    assert unignored_tags == {"command-instead-of-shell", "jinja[spacing]"}

    playbook.write_text(
        template.format(comment=" # noqa: command-instead-of-shell jinja[spacing]"),
        encoding="utf-8",
    )
    assert Runner(playbook, rules=default_rules_collection).run() == []

    playbook.write_text(
        template.format(comment=" # note about # noqa: command-instead-of-shell"),
        encoding="utf-8",
    )
    non_directive_tags = {
        match.tag for match in Runner(playbook, rules=default_rules_collection).run()
    }
    assert non_directive_tags == {"command-instead-of-shell", "jinja[spacing]"}


def test_block_scalar_noqa_edge_cases(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
) -> None:
    """Ensure null keys, explicit block-scalar keys, and !!omap do not misbehave."""
    vars_file = tmp_path / "roles" / "test_role" / "vars" / "main.yml"
    vars_file.parent.mkdir(parents=True)

    # 1. YAML null (`~`) key with block-scalar noqa must not collide with sentinel.
    vars_file.write_text(
        "---\n~: |- # noqa: jinja[spacing]\n  {{foo}}\n",
        encoding="utf-8",
    )
    null_lintable = Lintable(vars_file)
    null_data = append_skipped_rules({}, null_lintable)
    assert null_data[SKIPPED_RULES_KEY] == ["jinja[spacing]"]
    assert dict(null_lintable.line_skips) == {2: {"jinja[spacing]"}}
    null_tags = {
        match.tag for match in Runner(vars_file, rules=default_rules_collection).run()
    }
    assert "jinja[spacing]" not in null_tags

    # 2. Explicit block-scalar mapping key (? |-) must attribute line_skips to key line.
    vars_file.write_text(
        "---\n"
        "test_role_map:\n"
        "  ? |- # noqa: jinja[spacing]\n"
        "    {{foo}}\n"
        "  : >-\n"
        "    {{bar}}\n",
        encoding="utf-8",
    )
    explicit_lintable = Lintable(vars_file)
    append_skipped_rules({}, explicit_lintable)
    assert dict(explicit_lintable.line_skips) == {3: {"jinja[spacing]"}}
    explicit_matches = Runner(vars_file, rules=default_rules_collection).run()
    assert len(explicit_matches) == 1
    assert explicit_matches[0].tag == "jinja[spacing]"
    assert explicit_matches[0].lineno == 5

    # 3. !!omap (CommentedOrderedMap where lc.data is None) must not crash.
    vars_file.write_text(
        "---\n"
        "test_role_omap: !!omap\n"
        "  - test_role_a: |- # noqa: jinja[spacing]\n"
        "      {{foo}}\n",
        encoding="utf-8",
    )
    omap_lintable = Lintable(vars_file)
    omap_data = append_skipped_rules({}, omap_lintable)
    assert omap_data[SKIPPED_RULES_KEY] == ["jinja[spacing]"]
    assert Runner(vars_file, rules=default_rules_collection).run() == []


def test_block_scalar_noqa_fix_preserves_file(tmp_path: Path) -> None:
    """Ensure --fix preserves noqa block scalars even while rewriting other tasks."""
    vars_file = tmp_path / "roles" / "test_role" / "vars" / "main.yml"
    vars_file.parent.mkdir(parents=True)
    original = (
        "---\n"
        "some_var: >- # noqa: jinja[spacing] var-naming[no-role-prefix]\n"
        "  {{foo}}\n"
    )
    vars_file.write_text(original, encoding="utf-8")

    result = run_ansible_lint("--fix", str(vars_file))
    assert result.returncode == 0
    assert vars_file.read_text(encoding="utf-8") == original

    playbook = tmp_path / "playbook.yml"
    ignored_block = (
        "    - name: Keep ignored block scalar\n"
        "      changed_when: false\n"
        "      ansible.builtin.shell:\n"
        "        cmd: |- # noqa: command-instead-of-shell jinja[spacing]\n"
        '          echo "{{foo}}"\n'
    )
    playbook.write_text(
        "---\n"
        "- name: Test fix with block scalar noqa\n"
        "  hosts: localhost\n"
        "  tasks:\n"
        f"{ignored_block}"
        "\n"
        "    - name: fixable task name casing\n"
        "      ansible.builtin.debug:\n"
        "        msg: ok\n",
        encoding="utf-8",
    )
    fix_result = run_ansible_lint("--fix", str(playbook))
    assert fix_result.returncode == RC.FIXED_VIOLATIONS
    updated = playbook.read_text(encoding="utf-8")
    assert ignored_block in updated
    assert "    - name: Fixable task name casing\n" in updated
