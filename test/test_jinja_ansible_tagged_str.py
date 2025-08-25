"""Test cases for ansible-core _AnsibleTaggedStr error handling in jinja rule."""

from __future__ import annotations

import pytest
from ansible.errors import AnsibleError

from ansiblelint.rules.jinja import ignored_re


class TestAnsibleTaggedStrErrorHandling:
    """Test cases for _AnsibleTaggedStr error handling."""

    def test_jinja_cockpit_style_template_error_handling(self) -> None:
        """Test that cockpit-style templates with _AnsibleTaggedStr errors are properly ignored."""
        # Test _AnsibleTaggedStr error is ignored
        tagged_error = AnsibleError(
            'can only concatenate list (not "_AnsibleTaggedStr") to list'
        )
        assert ignored_re.search(str(tagged_error)), (
            f"_AnsibleTaggedStr error should be ignored: {tagged_error}"
        )

        # Test similar error without _AnsibleTaggedStr is NOT ignored
        normal_error = AnsibleError('can only concatenate list (not "str") to list')
        assert not ignored_re.search(str(normal_error)), (
            f"Normal error should not be ignored: {normal_error}"
        )

    @pytest.mark.skip(reason="Requires full environment setup")
    def test_jinja_template_generates_ansible_tagged_str_error_comprehensive(
        self,
    ) -> None:
        """Test comprehensive _AnsibleTaggedStr error generation and handling."""
        # This test is skipped because it requires full ansible-lint environment
        # The actual functionality is tested in the main jinja.py test

    @pytest.mark.parametrize(
        ("error_message", "should_be_ignored"),
        (
            ('can only concatenate list (not "_AnsibleTaggedStr") to list', True),
            ('can only concatenate str (not "_AnsibleTaggedStr") to str', True),
            ("Unexpected templating type error occurred on", True),
            ("Object of type method is not JSON serializable", True),
            ('can only concatenate list (not "int") to list', False),
            ("TemplateSyntaxError: unexpected char '!' at 5", False),
        ),
    )
    def test_jinja_ignore_patterns_comprehensive(
        self, error_message: str, should_be_ignored: bool
    ) -> None:
        """Test comprehensive ignore patterns for _AnsibleTaggedStr errors."""
        matches = bool(ignored_re.search(error_message))
        assert matches == should_be_ignored, (
            f"Error message '{error_message}' should {'be ignored' if should_be_ignored else 'not be ignored'} "
            f"but {'was' if matches else 'was not'} matched by ignore pattern"
        )
