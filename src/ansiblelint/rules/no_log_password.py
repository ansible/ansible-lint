# Copyright 2018, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""NoLogPasswordsRule used with ansible-lint."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule, RulesCollection, TransformMixin
from ansiblelint.runner import get_matches
from ansiblelint.transformer import Transformer
from ansiblelint.utils import Task, convert_to_boolean

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class NoLogPasswordsRule(AnsibleLintRule, TransformMixin):
    """Password should not be logged."""

    id = "no-log-password"
    description = (
        "When passing password argument you should have no_log configured "
        "to a non False value to avoid accidental leaking of secrets."
    )
    severity = "LOW"
    tags = ["opt-in", "security", "experimental"]
    version_added = "v5.0.9"

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        if task["action"]["__ansible_module_original__"] == "ansible.builtin.user" and (
            task["action"].get("password_lock") and not task["action"].get("password")
        ):
            has_password = False
        else:
            for param in task["action"]:
                if "password" in param:
                    has_password = True
                    break
            else:
                has_password = False

        has_loop = [key for key in task if key.startswith("with_") or key == "loop"]
        # No no_log and no_log: False behave the same way
        # and should return a failure (return True), so we
        # need to invert the boolean
        no_log = task.get("no_log", False)

        if (
            isinstance(no_log, str)
            and no_log.startswith("{{")
            and no_log.endswith("}}")
        ):
            # we cannot really evaluate jinja expressions
            return False

        return bool(
            has_password and not convert_to_boolean(no_log) and len(has_loop) > 0,
        )

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag == self.id:
            task = self.seek(match.yaml_path, data)
            task["no_log"] = True

            match.fixed = True


if "pytest" in sys.modules:
    from unittest import mock

    import pytest

    if TYPE_CHECKING:
        from ansiblelint.testing import RunFromText

    NO_LOG_UNUSED = """
- name: Test
  hosts: all
  tasks:
    - name: Succeed when no_log is not used but no loop present
      ansible.builtin.user:
        name: john_doe
        password: "wow"
        state: absent
"""

    NO_LOG_FALSE = """
- hosts: all
  tasks:
    - name: Use of jinja for no_log is valid
      user:
          name: john_doe
          user_password: "{{ item }}"
          state: absent
      no_log: "{{ False }}"
    - name: Fail when no_log is set to False
      user:
        name: john_doe
        user_password: "{{ item }}"
        state: absent
      with_items:
        - wow
        - now
      no_log: False
    - name: Fail when no_log is set to False
      ansible.builtin.user:
        name: john_doe
        user_password: "{{ item }}"
        state: absent
      with_items:
        - wow
        - now
      no_log: False
"""

    NO_LOG_NO = """
- hosts: all
  tasks:
    - name: Fail when no_log is set to no
      user:
        name: john_doe
        password: "{{ item }}"
        state: absent
      no_log: no
      loop:
        - wow
        - now
"""

    PASSWORD_WITH_LOCK = """
- hosts: all
  tasks:
    - name: Fail when password is set and password_lock is true
      user:
        name: "{{ item }}"
        password: "wow"
        password_lock: true
      with_random_choice:
        - ansible
        - lint
"""

    NO_LOG_YES = """
- hosts: all
  tasks:
    - name: Succeed when no_log is set to yes
      with_list:
        - name: user
          password: wow
        - password: now
          name: ansible
      user:
        name: "{{ item.name }}"
        password: "{{ item.password }}"
        state: absent
      no_log: yes
"""

    NO_LOG_TRUE = """
- hosts: all
  tasks:
    - name: Succeed when no_log is set to True
      user:
        name: john_doe
        user_password: "{{ item }}"
        state: absent
      no_log: True
      loop:
        - wow
        - now
"""

    PASSWORD_LOCK_YES = """
- hosts: all
  tasks:
    - name: Succeed when only password locking account
      user:
        name: "{{ item }}"
        password_lock: yes
        # user_password: "this is a comment, not a password"
        with_list:
          - ansible
          - lint
"""

    PASSWORD_LOCK_YES_BUT_NO_PASSWORD = """
- hosts: all
  tasks:
    - name: Succeed when only password locking account
      ansible.builtin.user:
        name: "{{ item }}"
        password_lock: yes
        # user_password: "this is a comment, not a password"
        with_list:
          - ansible
          - lint
"""

    PASSWORD_LOCK_FALSE = """
- hosts: all
  tasks:
    - name: Succeed when password_lock is false and password is not used
      user:
        name: lint
        password_lock: False
"""

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_unused(rule_runner: RunFromText) -> None:
        """The task does not use no_log but also no loop."""
        results = rule_runner.run_playbook(NO_LOG_UNUSED)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_false(rule_runner: RunFromText) -> None:
        """The task sets no_log to false."""
        results = rule_runner.run_playbook(NO_LOG_FALSE)
        assert len(results) == 2
        for result in results:
            assert result.rule.id == "no-log-password"

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_no(rule_runner: RunFromText) -> None:
        """The task sets no_log to no."""
        results = rule_runner.run_playbook(NO_LOG_NO)
        assert len(results) == 1
        assert results[0].rule.id == "no-log-password"

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_password_with_lock(rule_runner: RunFromText) -> None:
        """The task sets a password but also lock the user."""
        results = rule_runner.run_playbook(PASSWORD_WITH_LOCK)
        assert len(results) == 1
        assert results[0].rule.id == "no-log-password"

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_yes(rule_runner: RunFromText) -> None:
        """The task sets no_log to yes."""
        results = rule_runner.run_playbook(NO_LOG_YES)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_true(rule_runner: RunFromText) -> None:
        """The task sets no_log to true."""
        results = rule_runner.run_playbook(NO_LOG_TRUE)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_password_lock_yes(rule_runner: RunFromText) -> None:
        """The task only locks the user."""
        results = rule_runner.run_playbook(PASSWORD_LOCK_YES)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_no_log_password_lock_yes_but_no_password(rule_runner: RunFromText) -> None:
        """The task only locks the user."""
        results = rule_runner.run_playbook(PASSWORD_LOCK_YES_BUT_NO_PASSWORD)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "rule_runner",
        (NoLogPasswordsRule,),
        indirect=["rule_runner"],
    )
    def test_password_lock_false(rule_runner: RunFromText) -> None:
        """The task does not actually lock the user."""
        results = rule_runner.run_playbook(PASSWORD_LOCK_FALSE)
        assert len(results) == 0

    @mock.patch.dict(os.environ, {"ANSIBLE_LINT_WRITE_TMP": "1"}, clear=True)
    def test_no_log_password_transform(
        config_options: Options,
    ) -> None:
        """Test transform functionality for no-log-password rule."""
        playbook = Path("examples/playbooks/transform-no-log-password.yml")
        config_options.write_list = ["all"]
        rules = RulesCollection(options=config_options)
        rules.register(NoLogPasswordsRule())

        config_options.lintables = [str(playbook)]
        runner_result = get_matches(rules=rules, options=config_options)
        transformer = Transformer(result=runner_result, options=config_options)
        transformer.run()

        matches = runner_result.matches
        assert len(matches) == 2

        orig_content = playbook.read_text(encoding="utf-8")
        expected_content = playbook.with_suffix(
            f".transformed{playbook.suffix}",
        ).read_text(encoding="utf-8")
        transformed_content = playbook.with_suffix(f".tmp{playbook.suffix}").read_text(
            encoding="utf-8",
        )

        assert orig_content != transformed_content
        assert expected_content == transformed_content
        playbook.with_suffix(f".tmp{playbook.suffix}").unlink()
