import unittest
from subprocess import Popen, PIPE
import os
import shutil
import yaml


class TestCommandLineInvocationSameAsConfig(unittest.TestCase):
    def setUp(self):
        if os.path.exists(".sandbox"):
            shutil.rmtree(".sandbox")

        os.makedirs(".sandbox/subdir")

    def run_ansible_lint(self, args=False, config=None):
        command = "cd .sandbox; ../bin/ansible-lint ../test/skiptasks.yml"
        if args:
            command += " " + args

        if config:
            with open(".sandbox/.ansible-lint", "w") as outfile:
                yaml.dump(config, outfile, default_flow_style=False)

        result, err = Popen(
            [command],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        ).communicate()

        self.assertFalse(err, "Expected no error but was " + str(err))

        return result

    def assert_config_for(self, cli_arg, config):
        with_arg = self.run_ansible_lint(args=cli_arg)
        with_config = self.run_ansible_lint(config=config)

        self.assertEqual(with_arg, with_config)

    def test_parseable_as_config(self):
        self.assert_config_for("-p", dict(parseable=True))

    def test_quiet_as_config(self):
        self.assert_config_for("-q", dict(quiet=True))

    def test_rulesdir_as_config(self):
        self.assert_config_for("-r ../test/rules/", dict(rulesdir=["../test/rules/"]))

    def test_use_default_rules(self):
        self.assert_config_for("-R -r ../test/rules/", dict(rulesdir=["../test/rules"],
                                                            use_default_rules=True))

    def test_tags(self):
        self.assert_config_for("-t skip_ansible_lint", dict(tags=["skip_ansible_lint"]))

    def test_verbosity(self):
        self.assert_config_for("-v", dict(verbosity=1))

    def test_skip_list(self):
        self.assert_config_for("-x bad_tag", dict(skip_list=["bad_tag"]))

    def test_exclude(self):
        self.assert_config_for("--exclude ../test/", dict(exclude_paths=["../test/"]))

    def test_config_can_be_overridden(self):
        no_override = self.run_ansible_lint(args="-t bad_tag")
        overridden = self.run_ansible_lint(args="-t bad_tag", config=dict(tags=["skip_ansible_lint"]))

        self.assertEqual(no_override, overridden)

    def test_different_config_file(self):
        with open(".sandbox/subdir/ansible-config.yml", "w") as outfile:
            yaml.dump(dict(verbosity=1), outfile, default_flow_style=False)

        diff_config = self.run_ansible_lint(args="-c ./subdir/ansible-config.yml")
        no_config = self.run_ansible_lint(args="-v")

        self.assertEqual(diff_config, no_config)
