import tempfile
import shutil
import os

from ansiblelint import Runner


class RunFromText(object):
    """Use Runner on temp files created from unittest text snippets."""

    def __init__(self, collection):
        self.collection = collection

    def _call_runner(self, path):
        runner = Runner(self.collection, path, [], [], [])
        return runner.run()

    def run_playbook(self, playbook_text):
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(playbook_text.encode())
            fp.seek(0)
            results = self._call_runner(fp.name)
        return results

    def run_role_tasks_main(self, tasks_main_text):
        role_path = tempfile.mkdtemp(prefix='role_')
        tasks_path = os.path.join(role_path, 'tasks')
        os.makedirs(tasks_path)
        with open(os.path.join(tasks_path, 'main.yml'), 'w') as fp:
            fp.write(tasks_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results

    def run_role_meta_main(self, meta_main_text):
        role_path = tempfile.mkdtemp(prefix='role_')
        meta_path = os.path.join(role_path, 'meta')
        os.makedirs(meta_path)
        with open(os.path.join(meta_path, 'main.yml'), 'w') as fp:
            fp.write(meta_main_text)
        results = self._call_runner(role_path)
        shutil.rmtree(role_path)
        return results
