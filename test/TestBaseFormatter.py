# -*- coding: utf-8; -*-
from pathlib import Path
from typing import Any, Union

import pytest

from ansiblelint.formatters import BaseFormatter


@pytest.mark.parametrize(
    ('base_dir', 'relative_path'),
    (
        (None, True),
        ('/whatever', False),
        (Path('/whatever'), False),
    ),
)
@pytest.mark.parametrize('path', ('/whatever/string', Path('/whatever/string')))
def test_base_formatter_when_base_dir(
    base_dir: Any, relative_path: bool, path: str
) -> None:
    """Check that base formatter accepts relative pathlib and str."""
    # Given
    base_formatter = BaseFormatter(base_dir, relative_path)  # type: ignore

    # When
    output_path = base_formatter._format_path(path)

    # Then
    assert isinstance(output_path, str)
    assert base_formatter._base_dir is None or isinstance(base_formatter._base_dir, str)
    assert output_path == str(path)


@pytest.mark.parametrize(
    'base_dir',
    (
        Path('/whatever'),
        '/whatever',
    ),
)
@pytest.mark.parametrize('path', ('/whatever/string', Path('/whatever/string')))
def test_base_formatter_when_base_dir_is_given_and_relative_is_true(
    path: Union[str, Path], base_dir: Union[str, Path]
) -> None:
    """Check that the base formatter equally accepts pathlib and str."""
    # Given
    base_formatter = BaseFormatter(base_dir, True)  # type: ignore

    # When
    output_path = base_formatter._format_path(path)

    # Then
    assert isinstance(output_path, str)
    assert isinstance(base_formatter._base_dir, str)
    assert output_path == Path(path).name


# vim: et:sw=4:syntax=python:ts=4:
