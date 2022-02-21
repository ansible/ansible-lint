"""Tests for Transformer."""
from io import StringIO
from pathlib import Path
from typing import Tuple

import pytest
from ruamel.yaml import CommentedMap

from ansiblelint.runner import LintResult
from ansiblelint.skip_utils import load_data
from ansiblelint.transformer import Transformer

fixtures_dir = Path(__file__).parent / "fixtures"
formatting_before_fixtures_dir = fixtures_dir / "formatting-before"
formatting_after_fixtures_dir = fixtures_dir / "formatting-after"


@pytest.fixture
def empty_runner_result() -> LintResult:
    """Fixture that returns an empty LintResult."""
    return LintResult(matches=[], files=set())


@pytest.fixture
def empty_transformer(empty_runner_result: LintResult) -> Transformer:
    """Fixture that returns a Transformer initialized with an empty LintResult."""
    return Transformer(empty_runner_result)


@pytest.fixture
def yaml_formatting_fixture_before(
    fixture_filename: str,
) -> Tuple[Path, str, CommentedMap]:
    before_path = formatting_before_fixtures_dir / fixture_filename
    before_raw = before_path.read_text(encoding="utf-8")
    before_data = load_data(before_raw)
    return before_path, before_raw, before_data


@pytest.fixture
def yaml_formatting_fixture_after(
    fixture_filename: str,
) -> Tuple[Path, str, CommentedMap]:
    after_path = formatting_after_fixtures_dir / fixture_filename
    after_raw = after_path.read_text(encoding="utf-8")
    after_data = load_data(after_raw)
    return after_path, after_raw, after_data


@pytest.mark.parametrize(
    ("fixture_filename",),
    [
        ("fmt-1.yml",),
        ("fmt-2.yml",),
    ],
)
def test_transformer_yaml_reformat(
    empty_transformer: Transformer,
    yaml_formatting_fixture_before: Tuple[Path, str, CommentedMap],
    yaml_formatting_fixture_after: Tuple[Path, str, CommentedMap],
    fixture_filename: str,
) -> None:
    """Ensure that the Transformer produces output compatible with prettier."""
    # TODO: this is really ugly and needs to be refactored...
    before_path, before_raw, before_data = yaml_formatting_fixture_before
    after_path, after_raw, after_data = yaml_formatting_fixture_after

    with StringIO() as stream:
        empty_transformer.yaml.dump(before_data, stream)
        before_output = stream.getvalue()
    before_path.with_suffix(".transformed.yml").write_text(
        before_output, encoding="utf-8"
    )
    # before_transformed = before_path.with_suffix(".transformed.yml").read_text(encoding="utf-8")

    with StringIO() as stream:
        empty_transformer.yaml.dump(after_data, stream)
        after_output = stream.getvalue()
    after_path.with_suffix(".transformed.yml").write_text(
        after_output, encoding="utf-8"
    )
    # after_transformed = after_path.with_suffix(".transformed.yml").read_text(encoding="utf-8")

    # assert before_output == before_transformed
    # assert after_output == after_transformed
