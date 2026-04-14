"""Tests for vault secret initialization."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from ansible import constants as ansible_constants
from ansible.errors import AnsibleError

from ansiblelint import utils

if TYPE_CHECKING:
    from collections.abc import Iterator

# vault_encrypted.yml is encrypted with .vault_pass (secret123)
# and contains: {"my_secret": "test_value"}
VAULT_ENCRYPTED_FILE = str(
    Path(__file__).parent.parent / "examples/playbooks/vars/vault_encrypted.yml"
)


@pytest.fixture(autouse=True)  # cspell:ignore autouse
def _reset_vault_cache() -> Iterator[None]:
    """Reset the cached vault secrets between tests."""
    utils._vault_secrets = None  # noqa: SLF001
    yield
    utils._vault_secrets = None  # noqa: SLF001


def test_vault_secrets_loaded() -> None:
    """Vault secrets are loaded from ansible configuration."""
    secrets = utils._get_vault_secrets()  # noqa: SLF001
    assert len(secrets) >= 1
    _vault_id, secret = secrets[0]
    # Should be the real password from .vault_pass, not the dummy
    assert secret.bytes != b"x"


def test_vault_secrets_fallback() -> None:
    """Dummy password is returned when no vault configuration exists."""
    with patch.object(ansible_constants, "DEFAULT_VAULT_PASSWORD_FILE", None):
        secrets = utils._get_vault_secrets()  # noqa: SLF001
        assert len(secrets) == 1
        _vault_id, secret = secrets[0]
        assert secret.bytes == b"x"


def test_vault_secrets_bad_file() -> None:
    """Graceful fallback when vault password file does not exist."""
    with patch.object(
        ansible_constants,
        "DEFAULT_VAULT_PASSWORD_FILE",
        "/nonexistent/vault_pass",
    ):
        secrets = utils._get_vault_secrets()  # noqa: SLF001
        assert len(secrets) == 1
        _vault_id, secret = secrets[0]
        assert secret.bytes == b"x"


def test_vault_decrypt_with_password() -> None:
    """Vault-encrypted files are decrypted when password is available."""
    result = utils.parse_yaml_from_file(VAULT_ENCRYPTED_FILE)
    assert result is not None
    assert isinstance(result, dict)
    assert result["my_secret"] == "test_value"


def test_vault_decrypt_without_password() -> None:
    """Vault-encrypted files cannot be decrypted with the dummy password."""
    with (
        patch.object(ansible_constants, "DEFAULT_VAULT_PASSWORD_FILE", None),
        pytest.raises(AnsibleError, match="Decryption failed"),
    ):
        utils.parse_yaml_from_file(VAULT_ENCRYPTED_FILE)
