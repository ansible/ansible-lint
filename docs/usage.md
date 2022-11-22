(using-lint)=

# Using

```{contents} Topics

```

## Using commands

After you install Ansible-lint, run `ansible-lint --help` to display available commands and their options.

```{command-output} ansible-lint --help
   :cwd: ..
   :returncode: 0
```

### Command output

Ansible-lint prints output on both `stdout` and `stderr`.

- `stdout` displays rule violations.
- `stderr` displays logging and free-form messages like statistics.

Most `ansible-lint` examples use pep8 as the output format (`-p`) which is machine parseable.

Ansible-lint also print errors using their [annotation] format when it detects the `GITHUB_ACTIONS=true` and `GITHUB_WORKFLOW=...` variables.

[annotation]: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-error-message

## Caching

For optimal performance, Ansible-lint creates caches with installed or mocked roles, collections, and modules in the `{project_dir}/.cache` folder.
The location of `{project_dir}` is passed with a command line argument, determined by the location of the configuration file, git project top-level directory, or user home directory.

To perform faster re-runs, Ansible-lint does not automatically clean the cache.
If required you can do this manually by simply deleting the `.cache` folder.
Ansible-lint creates a new cache on the next invocation.

You should add the `.cache` folder to the `.gitignore` file in your git repositories.

## Using progressive mode

For easier adoption, Ansible-lint can alert for rule violations that occur since the last commit.
This allows new code to be merged without any rule violations while allowing content developers to address historical violations at a different pace.

The `--progressive` option runs Ansible-lint twice if rule violations exist in your content.
The second run is performed against a temporary git working copy that contains
the last commit.
Rule violations that exist in the last commit are ignored and Ansible-lint displays only the violations that exist in the new commit.

## Linting playbooks and roles

Ansible-lint recommends following the {ref}`collection structure layout <collection_structure>` whether you plan to build a collection or not.

Following that layout assures the best integration with all ecosystem tools because it helps those tools better distinguish between random YAML files and files managed by Ansible.
When you call `ansible-lint` without arguments, it uses internal heuristics to determine file types.

You can specify the list of **roles** or **playbooks** that you want to lint with the `-p` argument.
For example, to lint `examples/playbooks/play.yml` and `examples/roles/bobbins`, use the following command:

```{command-output} ansible-lint -p examples/playbooks/play.yml examples/roles/bobbins
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

## Running example playbooks

Ansible-lint includes an `ansible-lint/examples` folder that contains example playbooks with different rule violations and undesirable characteristics.
You can run `ansible-lint` on the example playbooks to observe Ansible-lint in action, as follows:

```{command-output} ansible-lint -p examples/playbooks/example.yml
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

Ansible-lint also handles playbooks that include other playbooks, tasks, handlers, or roles, as the `examples/playbooks/include.yml` example demonstrates.

```{command-output} ansible-lint --force-color --offline -p examples/playbooks/include.yml
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

You can generate `JSON` reports based on the codeclimate specification as the `examples/playbooks/norole.yml` example demonstrates.

```{command-output} ansible-lint -f json examples/playbooks/norole.yml
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

## Specifying rules at runtime

By default, `ansible-lint` applies rules found in `ansible-lint/src/ansiblelint/rules`.
Use the `-r /path/to/custom-rules` option to specify the directory path to a set of custom rules.
For multiple custom rule sets, pass each set with a separate `-r` option.

You can also combine the default rules with custom rules with the `-R` option along with one or more `-r` options.

### Including rules with tags

Each rule has an associated set of one or more tags.
Use the `-T` option to view the list of tags for each available rule.

You can then use the `-t` option to specify a tag and include the associated rules in the lint run.
For example, the following `ansible-lint` command applies only the rules associated with the _idempotency_ tag:

```bash
$ ansible-lint -t idempotency playbook.yml
```

The following shows the available tags in an example set of rules and the rules associated with each tag:

```{command-output} ansible-lint -T
   :cwd: ..
   :returncode: 0
   :nostderr: true
```

### Excluding rules with tags

To exclude rules by identifiers or tags, use the `-x SKIP_LIST` option.
For example, the following command applies all rules except those with the _formatting_ and _metadata_ tags:

```bash
$ ansible-lint -x formatting,metadata playbook.yml
```

### Ignoring rules

To only warn about rules, use the `-w WARN_LIST` option.
For example, the following command displays only warns about violations with rules associated with the `experimental` tag:

```console
$ ansible-lint -w experimental playbook.yml
```

By default, the `WARN_LIST` includes the `['experimental']` tag.
If you define a custom `WARN_LIST` you must add `'experimental'` so that Ansible-lint does not fail against experimental rules.

## Muting warnings to avoid false positives

Not all linting rules are precise, some are general rules of thumb.
Advanced _git_, _yum_ or _apt_ usage, for example, can be difficult to achieve in a playbook.
In cases like this, Ansible-lint can incorrectly trigger rule violations.

To disable rule violations for specific tasks, and mute false positives, add `# noqa [rule_id]` to the end of the line.
It is best practice to add a comment that explains why rules are disabled.

You can add the `# noqa [rule_id]` comment to the end of any line in a task.
You can also skip multiple rules with a space-separated list.

```yaml
- name: This task would typically fire git-latest and partial-become rules
  become_user: alice # noqa git-latest partial-become
  ansible.builtin.git: src=/path/to/git/repo dest=checkout
```

If the rule is line-based, `# noqa [rule_id]` must be at the end of the line.

```yaml
- name: This would typically fire LineTooLongRule 204 and jinja[spacing]
  get_url:
    url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf # noqa 204
    dest: "{{dest_proj_path}}/foo.conf" # noqa jinja[spacing]
```

If you want Ansible-lint to skip a rule entirely, use the `-x` command line argument or add it to `skip_list` in your configuration.

The least preferred method of skipping rules is to skip all task-based rules for a task, which does not skip line-based rules.
You can use the `skip_ansible_lint` tag with all tasks or the `warn` parameter with the _command_ or _shell_ modules, for example:

```yaml
- name: This would typically fire deprecated-command-syntax
  command: warn=no chmod 644 X

- name: This would typically fire command-instead-of-module
  command: git pull --rebase
  args:
    warn: false

- name: This would typically fire git-latest
  git: src=/path/to/git/repo dest=checkout
  tags:
    - skip_ansible_lint
```
