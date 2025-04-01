"""Types helper."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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

    TrustedAsTemplate = None

    class AnsibleTemplateSyntaxError:
        """Fake class introduced in 2.19."""

    ansible_error_format = 1
# core 2.19 + data tagging:
except ImportError:  # pragma: no cover
    # cspell: ignore datatag
    from ansible._internal._datatag._tags import (  # type: ignore[import-not-found,no-redef]
        TrustedAsTemplate,
    )
    from ansible._internal._yaml._constructor import (  # type: ignore[import-not-found,no-redef] # pyright: ignore[reportMissingImports] # pylint: disable=import-error,no-name-in-module
        AnsibleConstructor,
    )
    from ansible.errors import (  # type: ignore[no-redef,attr-defined,unused-ignore]
        AnsibleTemplateSyntaxError,  # pyright: ignore[reportAttributeAccessIssue]
    )

    AnsibleBaseYAMLObject: TypeAlias = (  # type: ignore[no-redef] # pyright: ignore[reportRedeclaration]
        AnsibleSequence
        | AnsibleMapping
        | AnsibleUnicode
        | str
        | Mapping
        | Sequence
        | None
    )
    ansible_error_format = 2
# temporary ignoring the type parameters for Sequence and Mapping because once
# add them we can no longer use isinstance() to check for them and we will
# need to implement a more complex runtime type checking.
AnsibleJSON: TypeAlias = Sequence | Mapping | AnsibleUnicode | str | None  # type: ignore[type-arg]

__all__ = [
    "AnsibleBaseYAMLObject",
    "AnsibleConstructor",
    "AnsibleJSON",
    "AnsibleMapping",
    "AnsibleSequence",
    "AnsibleTemplateSyntaxError",
    "AnsibleUnicode",
    "AnsibleVaultEncryptedUnicode",
    "TrustedAsTemplate",
    "ansible_error_format",
]
