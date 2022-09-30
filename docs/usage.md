(using-lint)=

# Usage

```{contents} Topics

```

## Command Line Options

The tool produces output on both `stdout` and `stderr`, first one being
used to display any matching rule violations while the second one being used
for logging and free form messages, like displaying stats.

In most of our examples we will be using the pep8 output format (`-p`) which
is machine parseable. The default output format is more verbose and likely
to contain more information, like long description of the rule and its
associated tags.

```{command-output} ansible-lint --help
   :cwd: ..
   :returncode: 0
```

## Temporary files

As part of the execution, the linter will likely need to create a cache of
installed or mocked roles, collections and modules. This is done inside
`{project_dir}/.cache` folder. The project directory is either given as a
command line argument, determined by location of the configuration
file, git project top-level directory or user home directory as fallback.
In order to speed-up reruns, the linter does not clean this folder by itself.

If you are using git, you will likely want to add this folder to your
`.gitignore` file.

## Progressive mode

In order to ease tool adoption, git users can enable the progressive mode using
`--progressive` option. This makes the linter return a success even if
some failures are found, as long the total number of violations did not
increase since the previous commit.

As expected, this mode makes the linter run twice if it finds any violations.
The second run is performed against a temporary git working copy that contains
the previous commit. All the violations that were already present are removed
from the list and the final result is displayed.

The most notable benefit introduced by this mode it does not prevent merging
new code while allowing developer to address historical violation at his own
speed.

## CI/CD

If execution under [Github Actions] is detected via the presence of
`GITHUB_ACTIONS=true` and `GITHUB_WORKFLOW=...` variables, the linter will
also print errors using their [annotation] format.

## Linting Playbooks and Roles

We recommend following the {ref}`collection structure layout <collection_structure>` regardless if you are planning to build a
collection or not. Following that layout assures the best integration
with all ecosystem tools as it helps them better distinguish between
random YAML files and files managed by ansible.

When you call ansible-lint without arguments the tool will use its internal
heuristics to determine file types.

`ansible-lint` also accepts a list of **roles** or **playbooks** as
arguments. The following command lints `examples/playbooks/play.yml` and
`examples/roles/bobbins` role:

```{command-output} ansible-lint -p examples/playbooks/play.yml examples/roles/bobbins
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

## Examples

Included in `ansible-lint/examples` are some example playbooks with
undesirable features. Running ansible-lint on them works, as demonstrated in
the following:

```{command-output} ansible-lint -p examples/playbooks/example.yml
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

If playbooks include other playbooks, or tasks, or handlers or roles, these
are also handled:

```{command-output} ansible-lint --force-color --offline -p examples/playbooks/include.yml
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

A `JSON` report, based on codeclimate specification, can be generated with
ansible-lint.

```{command-output} ansible-lint -f json examples/playbooks/norole.yml
   :cwd: ..
   :returncode: 2
   :nostderr: true
```

[annotation]: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-error-message
[github actions]: https://github.com/features/actions

## Specifying Rules at Runtime

By default, `ansible-lint` uses the rules found in
`ansible-lint/src/ansiblelint/rules`. To override this behavior and use a
custom set of rules, use the `-r /path/to/custom-rules` option to provide a
directory path containing the custom rules. For multiple rule sets, pass
multiple `-r` options.

It's also possible to use the default rules, plus custom rules. This can be
done by passing the `-R` to indicate that the default rules are to be used,
along with one or more `-r` options.

### Using Tags to Include Rules

Each rule has an associated set of one or more tags. To view the list of tags
for each available rule, use the `-T` option.

The following shows the available tags in an example set of rules, and the
rules associated with each tag:

```{command-output} ansible-lint -T
   :cwd: ..
   :returncode: 0
   :nostderr: true
```

To run just the _idempotency_ rules, for example, run the following:

```bash
$ ansible-lint -t idempotency playbook.yml
```

### Excluding Rules

To exclude rules using their identifiers or tags, use the `-x SKIP_LIST`
option. For example, the following runs all of the rules except those with the
tags _formatting_ and _metadata_:

```bash
$ ansible-lint -x formatting,metadata playbook.yml
```

### Ignoring Rules

To only warn about rules, use the `-w WARN_LIST` option. In this example all
rules are run, but if rules with the `experimental` tag match they only show
an error message but don't change the exit code:

```console
$ ansible-lint -w experimental playbook.yml
```

The default value for `WARN_LIST` is `['experimental']` if you don't
define your own either on the cli or in the config file. If you do define your
own `WARN_LIST` you will need to add `'experimental'` to it if you don't
want experimental rules to change your exit code.

## False Positives: Skipping Rules

Some rules are a bit of a rule of thumb. Advanced _git_, _yum_ or _apt_ usage,
for example, is typically difficult to achieve through the modules. In this
case, you should mark the task so that warnings aren't produced.

To skip a specific rule for a specific task, inside your ansible yaml add
`# noqa [rule_id]` at the end of the line. If the rule is task-based (most
are), add at the end of any line in the task. You can skip multiple rules via
a space-separated list.

```yaml
- name: This would typically fire git-latest and partial-become
  become_user: alice # noqa git-latest partial-become
  git: src=/path/to/git/repo dest=checkout
```

If the rule is line-based, `# noqa [rule_id]` must be at the end of the
particular line to be skipped

```yaml
- name: This would typically fire LineTooLongRule 204 and jinja[spacing]
  get_url:
    url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf # noqa 204
    dest: "{{dest_proj_path}}/foo.conf" # noqa jinja[spacing]
```

It's also a good practice to comment the reasons why a task is being skipped.

If you want skip running a rule entirely, you can use either use `-x` command
line argument, or add it to `skip_list` inside the configuration file.

A less-preferred method of skipping is to skip all task-based rules for a task
(this does not skip line-based rules). There are two mechanisms for this: the
`skip_ansible_lint` tag works with all tasks, and the `warn` parameter
works with the _command_ or _shell_ modules only. Examples:

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
