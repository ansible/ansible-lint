"""Types helper."""

from __future__ import annotations

from typing import TypeAlias

from ansible.parsing.yaml.objects import (  # pyright: ignore[reportMissingImports]
    AnsibleMapping,
    AnsibleSequence,
    AnsibleUnicode,
    AnsibleVaultEncryptedUnicode,
)

try:
    from ansible.parsing.yaml.constructor import (  # pyright: ignore[reportMissingImports]
        AnsibleConstructor,
    )
    from ansible.parsing.yaml.objects import (  # pyright: ignore[reportMissingImports]
        AnsibleBaseYAMLObject,  # pyright: ignore[reportRedeclaration]
    )
# core 2.19 + data tagging:
except ImportError:  # pragma: no cover
    from ansible._internal._yaml._constructor import (  # type: ignore[import-not-found,no-redef] # pyright: ignore[reportMissingImports] # pylint: disable=import-error,no-name-in-module
        AnsibleConstructor,
    )

    AnsibleBaseYAMLObject: TypeAlias = (  # type: ignore[no-redef] # pyright: ignore[reportRedeclaration]
        AnsibleSequence | AnsibleMapping | AnsibleUnicode | str | None
    )

AnsibleJSON: TypeAlias = AnsibleSequence | AnsibleMapping | AnsibleUnicode | str | None

__all__ = [
    "AnsibleBaseYAMLObject",
    "AnsibleConstructor",
    "AnsibleJSON",
    "AnsibleMapping",
    "AnsibleSequence",
    "AnsibleUnicode",
    "AnsibleVaultEncryptedUnicode",
]
