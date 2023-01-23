"""Rule definition to validate task options."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import logging
import re
import sys
from functools import lru_cache
from typing import Any

# pylint: disable=preferred-module
from unittest import mock
from unittest.mock import patch

# pylint: disable=reimported
import ansible.module_utils.basic as mock_ansible_module
from ansible.module_utils import basic
from ansible.plugins import loader

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.text import has_jinja
from ansiblelint.yaml_utils import clean_json

_logger = logging.getLogger(__name__)


@lru_cache
def load_module(module_name: str) -> loader.PluginLoadContext:
    """Load plugin from module name and cache it."""
    return loader.module_loader.find_plugin_with_context(module_name)


class ValidationPassed(Exception):
    """Exception to be raised when validation passes."""


class CustomAnsibleModule(basic.AnsibleModule):  # type: ignore
    """Mock AnsibleModule class."""

    def __init__(self, *args: str, **kwargs: str) -> None:
        """Initialize AnsibleModule mock."""
        super().__init__(*args, **kwargs)
        raise ValidationPassed


class ArgsRule(AnsibleLintRule):
    """Validating module arguments."""

    id = "args"
    severity = "HIGH"
    description = "Check whether tasks are using correct module options."
    tags = ["syntax", "experimental"]
    version_added = "v6.10.0"
    module_aliases: dict[str, str] = {"block/always/rescue": "block/always/rescue"}

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        # pylint: disable=too-many-branches,too-many-locals
        results: list[MatchError] = []
        module_name = task["action"]["__ansible_module_original__"]
        failed_msg = None

        if module_name in self.module_aliases:
            return []

        loaded_module = load_module(module_name)
        module_args = {
            key: value
            for key, value in task["action"].items()
            if not key.startswith("__")
        }

        with mock.patch.object(
            mock_ansible_module, "AnsibleModule", CustomAnsibleModule
        ):
            spec = importlib.util.spec_from_file_location(
                name=loaded_module.resolved_fqcn,
                location=loaded_module.plugin_resolved_path,
            )
            if spec:
                assert spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                assert file is not None
                _logger.warning(
                    "Unable to load module %s at %s:%s for options validation",
                    module_name,
                    file.filename,
                    task[LINE_NUMBER_KEY],
                )
                return []

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
                        basic._ANSIBLE_ARGS = None
                        try:
                            module.main()
                        except SystemExit:
                            failed_msg = fio.getvalue()
                    if failed_msg:
                        results.extend(
                            self._parse_failed_msg(failed_msg, task, module_name, file)
                        )

                sanitized_results = self._sanitize_results(results, module_name)
                return sanitized_results
            except ValidationPassed:
                return []

    def _sanitize_results(
        self, results: list[MatchError], module_name: str
    ) -> list[MatchError]:
        """Remove results that are false positive."""
        sanitized_results = []
        for result in results:
            result_msg = result.message
            if result_msg.startswith("Unsupported parameters"):
                # cmd option is a special case in command module and after option validation is done.
                if (
                    "Unsupported parameters for (basic.py) module" in result_msg
                    and module_name
                    in ["command", "ansible.builtin.command", "ansible.legacy.command"]
                ):
                    continue
                result.message = result_msg.replace("(basic.py)", f"{module_name}")
            elif result_msg.startswith("missing required arguments"):
                if (
                    "missing required arguments: free_form" in result_msg
                    and module_name
                    in [
                        "raw",
                        "ansible.builtin.raw",
                        "ansible.legacy.raw",
                        "meta",
                        "ansible.builtin.meta",
                        "ansible.legacy.meta",
                    ]
                ):
                    # free_form option is a special case in raw module hence ignore this error.
                    continue
                if (
                    "missing required arguments: key_value" in result_msg
                    and module_name
                    in [
                        "set_fact",
                        "ansible.builtin.set_fact",
                        "ansible.legacy.set_fact",
                    ]
                ):
                    # handle special case for set_fact module with key and value
                    continue
            if "Supported parameters include" in result_msg and module_name in [
                "set_fact",
                "ansible.builtin.set_fact",
                "ansible.legacy.set_fact",
            ]:
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
            r"argument '(?P<name>.*)' is of type", error_message
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
            r"value of (?P<name>.*) must be one of:", error_message
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
                linenumber=task[LINE_NUMBER_KEY],
                tag="args[module]",
                filename=file,
            )
        )
        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    def test_args_module_fail() -> None:
        """Test rule invalid module options."""
        collection = RulesCollection()
        collection.register(ArgsRule())
        success = "examples/playbooks/rule-args-module-fail-1.yml"
        results = Runner(success, rules=collection).run()
        assert len(results) == 5
        assert results[0].tag == "args[module]"
        assert "missing required arguments" in results[0].message
        assert results[1].tag == "args[module]"
        assert "missing parameter(s) required by " in results[1].message
        assert results[2].tag == "args[module]"
        assert "Unsupported parameters for" in results[2].message
        assert results[3].tag == "args[module]"
        assert "Unsupported parameters for" in results[2].message
        assert results[4].tag == "args[module]"
        assert "value of state must be one of" in results[4].message

    def test_args_module_pass() -> None:
        """Test rule valid module options."""
        collection = RulesCollection()
        collection.register(ArgsRule())
        success = "examples/playbooks/rule-args-module-pass-1.yml"
        results = Runner(success, rules=collection).run()
        assert len(results) == 0, results
