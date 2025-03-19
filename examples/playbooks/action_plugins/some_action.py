"""Sample action_plugin."""

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Sample module."""

    def run(self, tmp=None, task_vars=None):  # type: ignore[no-untyped-def]
        """."""
        super().run(tmp, task_vars)  # type: ignore[no-untyped-call]
        ret = {"foo": "bar"}
        return {"ansible_facts": ret}
