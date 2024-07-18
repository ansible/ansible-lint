"""Sample action_plugin."""

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):  # type: ignore[misc]
    """Sample module."""

    def run(self, tmp=None, task_vars=None):  # type: ignore[no-untyped-def]
        """."""
        super().run(tmp, task_vars)
        ret = {"foo": "bar"}
        return {"ansible_facts": ret}
