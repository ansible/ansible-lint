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
except ImportError:  # ansible-core 2.19+
    from ansible._internal._yaml._constructor import (  # pyright: ignore[reportMissingImports]
        AnsibleConstructor,
    )
try:
    from ansible.parsing.yaml.objects import (  # pyright: ignore[reportMissingImports]
        AnsibleBaseYAMLObject,  # pyright: ignore[reportRedeclaration]
    )
except ImportError:  # ansible-core 2.19+
    AnsibleBaseYAMLObject: TypeAlias = AnsibleSequence | AnsibleUnicode | str | None  # type: ignore[no-redef] # pyright: ignore[reportRedeclaration]


__all__ = [
    "AnsibleBaseYAMLObject",
    "AnsibleConstructor",
    "AnsibleMapping",
    "AnsibleSequence",
    "AnsibleUnicode",
    "AnsibleVaultEncryptedUnicode",
]
