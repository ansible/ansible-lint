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

from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import convert_to_boolean

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class NoLogPasswordsRule(AnsibleLintRule):
    id = "no-log-password"
    shortdesc = "password should not be logged."
    description = (
        "When passing password argument you should have no_log configured "
        "to a non False value to avoid accidental leaking of secrets."
    )
    severity = 'LOW'
    tags = ["security", "experimental"]
    version_added = "v5.0.9"

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:

        for param in task["action"].keys():
            if 'password' in param:
                has_password = True
                break
        else:
            has_password = False

        # No no_log and no_log: False behave the same way
        # and should return a failure (return True), so we
        # need to invert the boolean
        return bool(has_password and not convert_to_boolean(task.get('no_log', False)))
