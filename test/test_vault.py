"""Tests for vault secret initialization."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, NoReturn

import pytest
from ansible import constants as ansible_constants
from ansible.cli import CLI
from ansible.errors import AnsibleError

from ansiblelint import utils

if TYPE_CHECKING:
    from ansible.parsing.dataloader import DataLoader

# vault_encrypted.yml is encrypted with .vault_pass (secret123)
# and contains: {"my_secret": "test_value"}
VAULT_ENCRYPTED_FILE = str(
    Path(__file__).parent.parent / "examples/playbooks/vars/vault_encrypted.yml"
)


class _SystemExitModule(ModuleType):
    """Stand-in for ansible.cli that raises SystemExit on attribute access."""

    def __getattr__(self, name: str) -> NoReturn:
        """Mimic the import-time locale check in ansible.cli, which exits."""
        msg = "ERROR: Ansible requires the locale encoding to be UTF-8"
        raise SystemExit(msg)


def test_vault_secrets_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vault secrets are loaded from ansible configuration."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    secrets = utils._get_vault_secrets()  # noqa: SLF001
    assert len(secrets) >= 1
    _vault_id, secret = secrets[0]
    # Should be the real password from .vault_pass, not the dummy
    assert secret.bytes != b"x"


def test_vault_secrets_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dummy password is returned when no vault configuration exists."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    monkeypatch.setattr(ansible_constants, "DEFAULT_VAULT_PASSWORD_FILE", None)
    secrets = utils._get_vault_secrets()  # noqa: SLF001
    assert len(secrets) == 1
    _vault_id, secret = secrets[0]
    assert secret.bytes == b"x"


def test_vault_secrets_bad_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Graceful fallback when vault password file does not exist."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    monkeypatch.setattr(
        ansible_constants,
        "DEFAULT_VAULT_PASSWORD_FILE",
        "/nonexistent/vault_pass",
    )
    secrets = utils._get_vault_secrets()  # noqa: SLF001
    assert len(secrets) == 1
    _vault_id, secret = secrets[0]
    assert secret.bytes == b"x"


def test_vault_secrets_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dummy password is used when importing ansible.cli raises SystemExit."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    monkeypatch.setitem(sys.modules, "ansible.cli", _SystemExitModule("ansible.cli"))
    secrets = utils._get_vault_secrets()  # noqa: SLF001
    assert len(secrets) == 1
    _vault_id, secret = secrets[0]
    assert secret.bytes == b"x"


def test_vault_secrets_without_initialize_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Older setup_vault_secrets signatures without initialize_context work."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    fake_secrets: list[tuple[str, Any]] = [("default", object())]
    captured: dict[str, Any] = {"calls": 0}

    def fake_setup_vault_secrets(
        _loader: DataLoader,
        vault_ids: list[str],
        ask_vault_pass: bool,
        auto_prompt: bool,
    ) -> list[tuple[str, Any]]:
        """Match the setup_vault_secrets signature before ansible-core 2.19."""
        captured["calls"] += 1
        captured["vault_ids"] = vault_ids
        captured["ask_vault_pass"] = ask_vault_pass
        captured["auto_prompt"] = auto_prompt
        return fake_secrets

    monkeypatch.setattr(CLI, "setup_vault_secrets", fake_setup_vault_secrets)
    assert utils._get_vault_secrets() is fake_secrets  # noqa: SLF001
    assert utils._get_vault_secrets() is fake_secrets  # noqa: SLF001
    # A strict signature above also proves initialize_context was not passed.
    assert captured["calls"] == 1  # second call is served from the cache
    assert captured["ask_vault_pass"] is False
    assert captured["auto_prompt"] is False


def test_make_dataloader_without_set_vault_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A DataLoader lacking set_vault_secrets support is returned as-is."""

    class _PlainLoader:
        """DataLoader variant without vault secret support."""

    monkeypatch.setattr(utils, "DataLoader", _PlainLoader)
    loader = utils._make_dataloader()  # noqa: SLF001
    assert isinstance(loader, _PlainLoader)


def test_vault_decrypt_with_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vault-encrypted files are decrypted when password is available."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    result = utils.parse_yaml_from_file(VAULT_ENCRYPTED_FILE)
    assert result is not None
    assert isinstance(result, dict)
    assert result["my_secret"] == "test_value"


def test_vault_decrypt_without_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vault-encrypted files cannot be decrypted with the dummy password."""
    monkeypatch.setattr(utils, "_vault_secrets", None)
    monkeypatch.setattr(ansible_constants, "DEFAULT_VAULT_PASSWORD_FILE", None)
    with pytest.raises(AnsibleError, match="Decryption failed"):
        utils.parse_yaml_from_file(VAULT_ENCRYPTED_FILE)
