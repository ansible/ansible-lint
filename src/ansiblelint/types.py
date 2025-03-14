"""Types helper."""
from __future__ import annotations

from typing import Any, TypeAlias

from ansible.parsing.yaml.objects import (
    AnsibleMapping,
    AnsibleSequence,
    AnsibleUnicode,
    AnsibleVaultEncryptedUnicode,
)

try:
    from ansible.parsing.yaml.constructor import AnsibleConstructor
except ImportError:  # ansible-core 2.19+
    from ansible._internal._yaml._constructor import (  # pyright: ignore[reportMissingImports]
        AnsibleConstructor,
    )

AnsibleBaseYAMLObject: TypeAlias = dict[Any, Any] | str | list[Any]


__all__ = [
    "AnsibleBaseYAMLObject",
    "AnsibleConstructor",
    "AnsibleMapping",
    "AnsibleSequence",
    "AnsibleUnicode",
    "AnsibleVaultEncryptedUnicode",
]
