"""Tests for inline-env-var rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.inline_env_var import EnvVarsInCommandRule
from ansiblelint.testing import RunFromText

SUCCESS_PLAY_TASKS = """
- hosts: localhost

  tasks:
  - name: actual use of environment
    shell: echo $HELLO
    environment:
      HELLO: hello

  - name: use some key-value pairs
    command: chdir=/tmp creates=/tmp/bobbins warn=no touch bobbins

  - name: commands can have flags
    command: abc --xyz=def blah

  - name: commands can have equals in them
    command: echo "==========="

  - name: commands with cmd
    command:
      cmd:
        echo "-------"

  - name: command with stdin (ansible > 2.4)
    command: /bin/cat
    args:
      stdin: "Hello, world!"

  - name: use argv to send the command as a list
    command:
      argv:
        - /bin/echo
        - Hello
        - World

  - name: another use of argv
    command:
    args:
      argv:
        - echo
        - testing

  - name: environment variable with shell
    shell: HELLO=hello echo $HELLO

  - name: command with stdin_add_newline (ansible > 2.8)
    command: /bin/cat
    args:
      stdin: "Hello, world!"
      stdin_add_newline: false

  - name: command with strip_empty_ends (ansible > 2.8)
    command: echo
    args:
      strip_empty_ends: false
"""

FAIL_PLAY_TASKS = """
- hosts: localhost

  tasks:
  - name: environment variable with command
    command: HELLO=hello echo $HELLO

  - name: typo some stuff
    command: cerates=/tmp/blah warn=no touch /tmp/blah
"""


def test_success() -> None:
    """Positive test for inline-env-var."""
    collection = RulesCollection()
    collection.register(EnvVarsInCommandRule())
    runner = RunFromText(collection)
    results = runner.run_playbook(SUCCESS_PLAY_TASKS)
    assert len(results) == 0


def test_fail() -> None:
    """Negative test for inline-env-var."""
    collection = RulesCollection()
    collection.register(EnvVarsInCommandRule())
    runner = RunFromText(collection)
    results = runner.run_playbook(FAIL_PLAY_TASKS)
    assert len(results) == 2
