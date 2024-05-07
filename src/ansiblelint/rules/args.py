"""Rule definition to validate task options."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import logging
import re
import sys
from typing import TYPE_CHECKING, Any

# pylint: disable=preferred-module
from unittest import mock
from unittest.mock import patch

# pylint: disable=reimported
import ansible.module_utils.basic as mock_ansible_module
from ansible.module_utils import basic

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.text import has_jinja
from ansiblelint.utils import load_plugin
from ansiblelint.yaml_utils import clean_json

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


_logger = logging.getLogger(__name__)

ignored_re = re.compile(
    "|".join(  # noqa: FLY002
        [
            r"^parameters are mutually exclusive:",
            # https://github.com/ansible/ansible-lint/issues/3128 as strings can be jinja
            # Do not remove unless you manually test if the original example
            # from the bug does not trigger the rule anymore. We were not able
            # to add a regression test because it would involve installing this
            # collection. Attempts to reproduce same bug with other collections
            # failed, even if the message originates from Ansible core.
            r"^unable to evaluate string as dictionary$",
        ],
    ),
    flags=re.MULTILINE | re.DOTALL,
)

workarounds_drop_map = {
    # https://github.com/ansible/ansible-lint/issues/3110
    "ansible.builtin.copy": ["decrypt"],
    # https://github.com/ansible/ansible-lint/issues/2824#issuecomment-1354337466
    # https://github.com/ansible/ansible-lint/issues/3138
    "ansible.builtin.service": ["daemon_reload", "use"],
    # Avoid: Unsupported parameters for (basic.py) module: cmd. Supported parameters include: _raw_params, _uses_shell, argv, chdir, creates, executable, removes, stdin, stdin_add_newline, strip_empty_ends.
    "ansible.builtin.command": ["cmd"],
    # https://github.com/ansible/ansible-lint/issues/3152
    "ansible.posix.synchronize": ["use_ssh_args"],
}
workarounds_inject_map = {
    # https://github.com/ansible/ansible-lint/issues/2824
    "ansible.builtin.async_status": {"_async_dir": "/tmp/ansible-async"},
}


class ValidationPassedError(Exception):
    """Exception to be raised when validation passes."""


class CustomAnsibleModule(basic.AnsibleModule):  # type: ignore[misc]
    """Mock AnsibleModule class."""

    def __init__(self, *args: str, **kwargs: str) -> None:
        """Initialize AnsibleModule mock."""
        super().__init__(*args, **kwargs)
        raise ValidationPassedError


class ArgsRule(AnsibleLintRule):
    """Validating module arguments."""

    id = "args"
    severity = "HIGH"
    description = "Check whether tasks are using correct module options."
    tags = ["syntax", "experimental"]
    version_added = "v6.10.0"
    module_aliases: dict[str, str] = {"block/always/rescue": "block/always/rescue"}
    _ids = {
        "args[module]": description,
    }

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        # pylint: disable=too-many-return-statements
        results: list[MatchError] = []
        module_name = task["action"]["__ansible_module_original__"]
        failed_msg = None

        if module_name in self.module_aliases:
            return []

        loaded_module = load_plugin(module_name)

        # https://github.com/ansible/ansible-lint/issues/3200
        # since "ps1" modules cannot be executed on POSIX platforms, we will
        # avoid running this rule for such modules
        if isinstance(
            loaded_module.plugin_resolved_path,
            str,
        ) and loaded_module.plugin_resolved_path.endswith(".ps1"):
            return []

        module_args = {
            key: value
            for key, value in task["action"].items()
            if not key.startswith("__")
        }

        # Return if 'args' is jinja string
        # https://github.com/ansible/ansible-lint/issues/3199
        if (
            "args" in task.raw_task
            and isinstance(task.raw_task["args"], str)
            and has_jinja(task.raw_task["args"])
        ):
            return []

        if loaded_module.resolved_fqcn in workarounds_inject_map:
            module_args.update(workarounds_inject_map[loaded_module.resolved_fqcn])
        if loaded_module.resolved_fqcn in workarounds_drop_map:
            for key in workarounds_drop_map[loaded_module.resolved_fqcn]:
                if key in module_args:
                    del module_args[key]

        with mock.patch.object(
            mock_ansible_module,
            "AnsibleModule",
            CustomAnsibleModule,
        ):
            spec = importlib.util.spec_from_file_location(
                name=loaded_module.resolved_fqcn,
                location=loaded_module.plugin_resolved_path,
            )
            if not spec:
                assert file is not None
                _logger.warning(
                    "Unable to load module %s at %s:%s for options validation",
                    module_name,
                    file.filename,
                    task[LINE_NUMBER_KEY],
                )
                return []
            assert spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            try:
                if not hasattr(module, "main"):
                    # skip validation for module options that are implemented as action plugin
                    # as the option values can be changed in action plugin and are not passed
                    # through `ArgumentSpecValidator` class as in case of modules.
                    return []

                with patch.object(
                    sys,
                    "argv",
                    ["", json.dumps({"ANSIBLE_MODULE_ARGS": clean_json(module_args)})],
                ):
                    fio = io.StringIO()
                    failed_msg = ""
                    # Warning: avoid running anything while stdout is redirected
                    # as what happens may be very hard to debug.
                    with contextlib.redirect_stdout(fio):
                        # pylint: disable=protected-access
                        basic._ANSIBLE_ARGS = None  # noqa: SLF001
                        try:
                            module.main()
                        except SystemExit:
                            failed_msg = fio.getvalue()
                    if failed_msg:
                        results.extend(
                            self._parse_failed_msg(failed_msg, task, module_name, file),
                        )

                sanitized_results = self._sanitize_results(results, module_name)
            except ValidationPassedError:
                return []
            return sanitized_results

    # pylint: disable=unused-argument
    def _sanitize_results(
        self,
        results: list[MatchError],
        module_name: str,
    ) -> list[MatchError]:
        """Remove results that are false positive."""
        sanitized_results = []
        for result in results:
            result_msg = result.message
            if ignored_re.match(result_msg):
                continue
            sanitized_results.append(result)

        return sanitized_results

    def _parse_failed_msg(
        self,
        failed_msg: str,
        task: dict[str, Any],
        module_name: str,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        """Parse failed message and return list of MatchError."""
        results: list[MatchError] = []
        try:
            failed_obj = json.loads(failed_msg)
            error_message = failed_obj["msg"]
        except json.decoder.JSONDecodeError:
            error_message = failed_msg

        option_type_check_error = re.search(
            r"argument '(?P<name>.*)' is of type",
            error_message,
        )
        if option_type_check_error:
            # ignore options with templated variable value with type check errors
            option_key = option_type_check_error.group("name")
            option_value = task["action"][option_key]
            if has_jinja(option_value):
                _logger.debug(
                    "Type checking ignored for '%s' option in task '%s' at line %s.",
                    option_key,
                    module_name,
                    task[LINE_NUMBER_KEY],
                )
                return results

        value_not_in_choices_error = re.search(
            r"value of (?P<name>.*) must be one of:",
            error_message,
        )
        if value_not_in_choices_error:
            # ignore templated value not in allowed choices
            choice_key = value_not_in_choices_error.group("name")
            choice_value = task["action"][choice_key]
            if has_jinja(choice_value):
                _logger.debug(
                    "Value checking ignored for '%s' option in task '%s' at line %s.",
                    choice_key,
                    module_name,
                    task[LINE_NUMBER_KEY],
                )
                return results

        results.append(
            self.create_matcherror(
                message=error_message,
                lineno=task[LINE_NUMBER_KEY],
                tag="args[module]",
                filename=file,
            ),
        )
        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest  # noqa: TCH002

    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    def test_args_module_fail(default_rules_collection: RulesCollection) -> None:
        """Test rule invalid module options."""
        success = "examples/playbooks/rule-args-module-fail.yml"
        results = Runner(success, rules=default_rules_collection).run()
        assert len(results) == 5
        assert results[0].tag == "args[module]"
        assert "missing required arguments" in results[0].message
        assert results[1].tag == "args[module]"
        assert "missing parameter(s) required by " in results[1].message
        assert results[2].tag == "args[module]"
        assert "Unsupported parameters for" in results[2].message
        assert results[3].tag == "args[module]"
        assert "Unsupported parameters for" in results[3].message
        assert results[4].tag == "args[module]"
        assert "value of state must be one of" in results[4].message

    def test_args_module_pass(
        default_rules_collection: RulesCollection,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test rule valid module options."""
        success = "examples/playbooks/rule-args-module-pass.yml"
        with caplog.at_level(logging.WARNING):
            results = Runner(success, rules=default_rules_collection).run()
        assert len(results) == 0, results
        assert len(caplog.records) == 0, caplog.records
