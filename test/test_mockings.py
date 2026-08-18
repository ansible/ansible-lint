"""Test mockings module."""

from pathlib import Path

import pytest

from ansiblelint._mockings import _make_module_stub
from ansiblelint.config import Options
from ansiblelint.constants import RC
from ansiblelint.testing import run_ansible_lint


def test_make_module_stub(config_options: Options) -> None:
    """Test make module stub."""
    config_options.cache_dir = Path()  # current directory
    with pytest.raises(SystemExit) as exc:
        _make_module_stub(module_name="", options=config_options)
    assert exc.type is SystemExit
    assert exc.value.code == RC.INVALID_CONFIG


def test_mock_roles_with_collection_name(tmp_path: Path) -> None:
    """Test mock_roles with collection role names (namespace.collection.role).

    See https://github.com/ansible/ansible-lint/issues/4973
    """
    (tmp_path / ".ansible-lint.yml").write_text("mock_roles:\n  - ns.coll.role\n")
    (tmp_path / "playbook.yml").write_text(
        "---\n- name: Test\n  hosts: localhost\n  roles:\n    - ns.coll.role\n"
    )
    result = run_ansible_lint("playbook.yml", cwd=tmp_path, offline=False)
    assert "was not found" not in result.stdout


def test_add_collections_path_if_needed(tmp_path: Path) -> None:
    """Test _add_collections_path_if_needed helper."""
    from ansiblelint.app import _add_collections_path_if_needed

    options = Options()
    options.cache_dir = tmp_path
    options.mock_roles = ["ns.coll.role"]
    paths: list[str] = ["/existing/collections"]

    _add_collections_path_if_needed(options, paths)
    mock_path = str(tmp_path / "ansible-lint-mocks" / "collections")
    assert paths == ["/existing/collections", mock_path]

    _add_collections_path_if_needed(options, paths)
    assert paths.count(mock_path) == 1

    options.mock_roles = ["simple"]
    paths2: list[str] = []
    _add_collections_path_if_needed(options, paths2)
    assert not paths2


def test_options_collection_mocks() -> None:
    """Test Options.has_collection_mocks and mock path helpers."""
    opts = Options()
    opts.cache_dir = None
    assert opts.mock_root is None
    assert opts.mock_collections_path is None
    assert opts.mock_modules_path is None

    opts.cache_dir = Path("/tmp/cache")
    opts.mock_modules = ["ns.coll.mod"]
    assert opts.has_collection_mocks() is True
    assert opts.mock_root == Path("/tmp/cache/ansible-lint-mocks")
    assert opts.mock_collections_path == Path(
        "/tmp/cache/ansible-lint-mocks/collections",
    )
    assert opts.mock_modules_path == Path("/tmp/cache/ansible-lint-mocks/modules")


def test_mock_modules_stub_is_lintable(tmp_path: Path) -> None:
    """Ensure generated mock module docs do not trip yaml/doc parsing."""
    (tmp_path / ".ansible-lint.yml").write_text(
        "mock_modules:\n  - some_ns.some_coll.some_module\n"
    )
    (tmp_path / "playbook.yml").write_text(
        "---\n"
        "- name: Test mocked module\n"
        "  hosts: localhost\n"
        "  gather_facts: false\n"
        "  tasks:\n"
        "    - name: Run mocked module\n"
        "      some_ns.some_coll.some_module:\n"
    )
    result = run_ansible_lint("playbook.yml", cwd=tmp_path)
    assert result.returncode == 0, result.stdout


def test_short_mock_modules_stub_is_lintable(tmp_path: Path) -> None:
    """Ensure short-name mock modules are resolved during syntax-check."""
    (tmp_path / ".ansible-lint.yml").write_text("mock_modules:\n  - custom_module\n")
    (tmp_path / "playbook.yml").write_text(
        "---\n"
        "- name: Test mocked short module\n"
        "  hosts: localhost\n"
        "  gather_facts: false\n"
        "  tasks:\n"
        "    - name: Run mocked short module\n"
        "      custom_module:\n"
    )
    result = run_ansible_lint("playbook.yml", cwd=tmp_path)
    assert result.returncode == 0, result.stdout


def test_mock_modules_do_not_overwrite_installed_module(
    config_options: Options,
    tmp_path: Path,
) -> None:
    """Mock stubs must not overwrite a real installed module file."""
    from ansiblelint._mockings import _make_module_stub
    from ansiblelint.constants import MOCK_MODULE_MARKER

    config_options.cache_dir = tmp_path
    real_module = (
        tmp_path
        / "ansible-lint-mocks"
        / "collections"
        / "ansible_collections"
        / "ns"
        / "coll"
        / "plugins"
        / "modules"
        / "installed.py"
    )
    real_module.parent.mkdir(parents=True)
    original = (
        "#!/usr/bin/python\n# real module\nARGUMENT_SPEC = {'name': {'type': 'str'}}\n"
    )
    real_module.write_text(original, encoding="utf-8")

    _make_module_stub(module_name="ns.coll.installed", options=config_options)

    assert real_module.read_text(encoding="utf-8") == original
    assert MOCK_MODULE_MARKER not in original


def test_mock_modules_do_not_touch_real_collections_tree(
    config_options: Options,
    tmp_path: Path,
) -> None:
    """Offline-style mocks must write under ansible-lint-mocks, not collections/."""
    from ansiblelint._mockings import _make_module_stub, is_lint_mock_module
    from ansiblelint.constants import MOCK_MODULE_MARKER

    config_options.cache_dir = tmp_path
    real_module = (
        tmp_path
        / "collections"
        / "ansible_collections"
        / "ns"
        / "coll"
        / "plugins"
        / "modules"
        / "sample.py"
    )
    real_module.parent.mkdir(parents=True)
    original = "#!/usr/bin/python\n# installed collection module\n"
    real_module.write_text(original, encoding="utf-8")

    _make_module_stub(module_name="ns.coll.sample", options=config_options)

    assert real_module.read_text(encoding="utf-8") == original
    stub = (
        tmp_path
        / "ansible-lint-mocks"
        / "collections"
        / "ansible_collections"
        / "ns"
        / "coll"
        / "plugins"
        / "modules"
        / "sample.py"
    )
    assert stub.is_file()
    assert is_lint_mock_module(stub)
    assert stub.read_text(encoding="utf-8").startswith(MOCK_MODULE_MARKER)


def test_args_rule_skips_lint_mock_modules(tmp_path: Path) -> None:
    """ArgsRule must not validate empty mock_modules stubs."""
    (tmp_path / ".ansible-lint.yml").write_text(
        "---\n"
        "mock_modules:\n"
        "  - fake_ns.fake_coll.fake_module\n"
        "enable_list:\n"
        "  - args\n"
        "skip_list:\n"
        "  - name[missing]\n"
    )
    (tmp_path / "playbook.yml").write_text(
        "---\n"
        "- name: Test mocked module args\n"
        "  hosts: localhost\n"
        "  gather_facts: false\n"
        "  tasks:\n"
        "    - name: Call mocked module with args\n"
        "      fake_ns.fake_coll.fake_module:\n"
        "        foo: bar\n"
        "        baz: 1\n"
    )
    result = run_ansible_lint("playbook.yml", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "args[module]" not in result.stdout
    assert "Unsupported parameters" not in result.stdout


def test_is_lint_mock_module_detects_marker(tmp_path: Path) -> None:
    """Marker-based detection covers legacy stubs outside ansible-lint-mocks."""
    from ansiblelint._mockings import is_lint_mock_module
    from ansiblelint.constants import MOCK_MODULE_MARKER

    stub = tmp_path / "ad_hoc_command.py"
    stub.write_text(
        f"{MOCK_MODULE_MARKER}\nfrom ansible.module_utils.basic import AnsibleModule\n",
    )
    real = tmp_path / "real.py"
    real.write_text("#!/usr/bin/python\n# real\n")

    assert is_lint_mock_module(stub) is True
    assert is_lint_mock_module(real) is False
    assert is_lint_mock_module(None) is False


def test_perform_mockings_cleanup_removes_module_stubs(
    config_options: Options,
    tmp_path: Path,
) -> None:
    """Cleanup removes lint-generated module stubs under the mocks root."""
    from ansiblelint._mockings import _make_module_stub, _perform_mockings_cleanup

    config_options.cache_dir = tmp_path
    config_options.mock_modules = ["ns.coll.sample", "custom_sample"]
    _make_module_stub(module_name="ns.coll.sample", options=config_options)
    _make_module_stub(module_name="custom_sample", options=config_options)

    fqcn_stub = (
        tmp_path
        / "ansible-lint-mocks"
        / "collections"
        / "ansible_collections"
        / "ns"
        / "coll"
        / "plugins"
        / "modules"
        / "sample.py"
    )
    short_stub = tmp_path / "ansible-lint-mocks" / "modules" / "custom_sample.py"
    assert fqcn_stub.is_file()
    assert short_stub.is_file()

    _perform_mockings_cleanup(config_options)
    assert not fqcn_stub.exists()
    assert not short_stub.exists()


def test_mock_roles_reject_path_escape(
    config_options: Options,
    tmp_path: Path,
) -> None:
    """Simple mock_roles values must not escape the mocks root."""
    from ansiblelint._mockings import _perform_mockings
    from ansiblelint.constants import RC

    config_options.cache_dir = tmp_path
    config_options.mock_roles = ["../../outside"]
    with pytest.raises(SystemExit) as exc:
        _perform_mockings(options=config_options)
    assert exc.value.code == RC.INVALID_CONFIG
    assert not (tmp_path / "outside").exists()


def test_warn_if_mock_clobbered_real_collections(
    config_options: Options,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Warn when legacy mock stubs remain under the real collections tree."""
    from ansiblelint._mockings import _perform_mockings
    from ansiblelint.constants import MOCK_MODULE_MARKER

    config_options.cache_dir = tmp_path
    config_options.mock_modules = ["ns.coll.sample"]
    legacy_stub = (
        tmp_path
        / "collections"
        / "ansible_collections"
        / "ns"
        / "coll"
        / "plugins"
        / "modules"
        / "sample.py"
    )
    legacy_stub.parent.mkdir(parents=True)
    legacy_stub.write_text(
        f"{MOCK_MODULE_MARKER}\nfrom ansible.module_utils.basic import AnsibleModule\n",
        encoding="utf-8",
    )

    with caplog.at_level("WARNING"):
        _perform_mockings(options=config_options)

    assert "Found ansible-lint mock stub at" in caplog.text
    assert "Reinstall affected collections" in caplog.text


def test_safe_path_under_root_rejects_invalid_parts(tmp_path: Path) -> None:
    """Path helper rejects traversal and separator injection."""
    from ansiblelint._mockings import _safe_path_under_root

    root = tmp_path / "ansible-lint-mocks"
    root.mkdir()

    assert _safe_path_under_root(root, "roles", "valid_role") is not None
    assert _safe_path_under_root(root, "roles", "..", "outside") is None
    assert _safe_path_under_root(root, "roles", "nested/role") is None
    assert _safe_path_under_root(root, "roles", "") is None


def test_safe_path_under_root_rejects_symlink_escape(tmp_path: Path) -> None:
    """Resolved paths outside the mocks root are rejected."""
    from ansiblelint._mockings import _safe_path_under_root

    root = tmp_path / "ansible-lint-mocks"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "roles").symlink_to(outside)

    assert _safe_path_under_root(root, "roles", "escaped") is None


def test_is_lint_mock_module_handles_missing_file_and_oserror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-files and unreadable paths are not treated as lint mocks."""
    from ansiblelint._mockings import is_lint_mock_module

    assert is_lint_mock_module(tmp_path) is False

    module_path = tmp_path / "module.py"
    module_path.write_text("# stub\n", encoding="utf-8")

    def raise_oserror(*_args: object, **_kwargs: object) -> None:
        msg = "permission denied"
        raise OSError(msg)

    monkeypatch.setattr(Path, "open", raise_oserror)
    assert is_lint_mock_module(module_path) is False


def test_make_module_stub_requires_cache_dir(config_options: Options) -> None:
    """Module stub creation fails fast when cache_dir is unset."""
    config_options.cache_dir = None
    with pytest.raises(RuntimeError, match="Cache directory not set"):
        _make_module_stub(module_name="ns.coll.mod", options=config_options)


def test_mock_roles_reject_invalid_names(
    config_options: Options,
    tmp_path: Path,
) -> None:
    """Invalid mock_roles names are rejected before touching disk."""
    from ansiblelint._mockings import _perform_mockings
    from ansiblelint.constants import RC

    config_options.cache_dir = tmp_path
    config_options.mock_roles = ["bad/role"]
    with pytest.raises(SystemExit) as exc:
        _perform_mockings(options=config_options)
    assert exc.value.code == RC.INVALID_CONFIG


def test_perform_mockings_cleanup_removes_collection_roles(
    config_options: Options,
    tmp_path: Path,
) -> None:
    """Cleanup removes collection role directories under the mocks root."""
    from ansiblelint._mockings import _perform_mockings, _perform_mockings_cleanup

    config_options.cache_dir = tmp_path
    config_options.mock_roles = ["ns.coll.role"]
    _perform_mockings(options=config_options)

    role_path = (
        tmp_path
        / "ansible-lint-mocks"
        / "collections"
        / "ansible_collections"
        / "ns"
        / "coll"
        / "roles"
        / "role"
    )
    assert role_path.is_dir()

    _perform_mockings_cleanup(config_options)
    assert not role_path.exists()


def test_perform_mockings_cleanup_requires_cache_dir(config_options: Options) -> None:
    """Cleanup fails fast when cache_dir is unset."""
    from ansiblelint._mockings import _perform_mockings_cleanup

    config_options.cache_dir = None
    with pytest.raises(RuntimeError, match="Cache directory not set"):
        _perform_mockings_cleanup(config_options)


def test_warn_if_mock_clobbered_skips_short_module_names(
    config_options: Options,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Legacy-clobber warning only applies to collection module paths."""
    from ansiblelint._mockings import _warn_if_mock_clobbered_real_collections

    config_options.cache_dir = tmp_path
    config_options.mock_modules = ["plain_module"]

    with caplog.at_level("WARNING"):
        _warn_if_mock_clobbered_real_collections(config_options)

    assert caplog.text == ""
