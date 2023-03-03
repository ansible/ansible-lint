# Using

## Using commands

After you install Ansible-lint, run `ansible-lint --help` to display available
commands and their options.

```console exec="1" source="console"
$ ansible-lint --help
```

### Command output

Ansible-lint prints output on both `stdout` and `stderr`.

- `stdout` displays rule violations.
- `stderr` displays logging and free-form messages like statistics.

Most `ansible-lint` examples use pep8 as the output format (`-p`) which is
machine parseable.

Ansible-lint also print errors using their [annotation] format when it detects
the `GITHUB_ACTIONS=true` and `GITHUB_WORKFLOW=...` variables.

[annotation]:
  https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-error-message

## Caching

For optimal performance, Ansible-lint creates caches with installed or mocked
roles, collections, and modules in the `{project_dir}/.cache` folder. The
location of `{project_dir}` is passed with a command line argument, determined
by the location of the configuration file, git project top-level directory, or
user home directory.

To perform faster re-runs, Ansible-lint does not automatically clean the cache.
If required you can do this manually by simply deleting the `.cache` folder.
Ansible-lint creates a new cache on the next invocation.

You should add the `.cache` folder to the `.gitignore` file in your git
repositories.

## Using progressive mode (deprecated)

!!! warning

    This feature is deprecated and will be removed in the next major release.
    We encourage you to use [ignore file](configuring.md#ignoring-rules-for-entire-files)
    instead.

For easier adoption, Ansible-lint can alert for rule violations that occur since
the last commit. This allows new code to be merged without any rule violations
while allowing content developers to address historical violations at a
different pace.

The `--progressive` option runs Ansible-lint twice if rule violations exist in
your content. The second run is performed against a temporary git working copy
that contains the last commit. Rule violations that exist in the last commit are
ignored and Ansible-lint displays only the violations that exist in the new
commit.

## Linting playbooks and roles

Ansible-lint recommends following the
{ref}`collection structure layout <collection_structure>` whether you plan to
build a collection or not.

Following that layout assures the best integration with all ecosystem tools
because it helps those tools better distinguish between random YAML files and
files managed by Ansible. When you call `ansible-lint` without arguments, it
uses internal heuristics to determine file types.

You can specify the list of **roles** or **playbooks** that you want to lint
with the `-p` argument. For example, to lint `examples/playbooks/play.yml` and
`examples/roles/bobbins`, use the following command:

```console exec="1" source="console" returncode="2"
$ ansible-lint --offline -p examples/playbooks/play.yml examples/roles/bobbins
```

## Running example playbooks

Ansible-lint includes an `ansible-lint/examples` folder that contains example
playbooks with different rule violations and undesirable characteristics. You
can run `ansible-lint` on the example playbooks to observe Ansible-lint in
action, as follows:

```console exec="1" source="console" returncode="2"
$ ansible-lint --offline -p examples/playbooks/example.yml
```

Ansible-lint also handles playbooks that include other playbooks, tasks,
handlers, or roles, as the `examples/playbooks/include.yml` example
demonstrates.

```console exec="1" source="console" returncode="2"
$ ansible-lint --offline -q -p examples/playbooks/include.yml
```

## Output formats

### pep8

```console exec="1" source="console" returncode="2"
$ ansible-lint --offline -q -f pep8 examples/playbooks/norole.yml
```

### SARIF JSON

Using `--format sarif` or `--format json` the linter will output on stdout a
report in [SARIF]

We also have an option `--sarif-file FILE` option that can make the linter dump
the output to a file while not altering its normal stdout output. This can be
used in CI/CD pipelines.

```bash exec="1" source="tabbed-left" result="json" returncode="2"
ansible-lint --offline -q -f sarif examples/playbooks/norole.yml
```

### Code Climate JSON

You can generate `JSON` reports based on the [Code Climate] specification as the
`examples/playbooks/norole.yml` example demonstrates.

```bash exec="1" source="tabbed-left" result="json" returncode="2"
ansible-lint --offline -q -f codeclimate examples/playbooks/norole.yml
```

Historically `-f json` was used to generate Code Climate JSON reports but in
never versions we switched its meaning point SARIF JSON format instead.

!!! warning

    When possible we recommend using the [SARIF](#sarif-json) format instead of the Code Climate
    as that one is more complete and has a full specification and also a JSON
    validation schema. Code Climate format does not expose our severity
    levels because we use that field to map warnings
    as `minor` and errors as `major` issues.

## Specifying rules at runtime

By default, `ansible-lint` applies rules found in
`ansible-lint/src/ansiblelint/rules`. Use the `-r /path/to/custom-rules` option
to specify the directory path to a set of custom rules. For multiple custom rule
sets, pass each set with a separate `-r` option.

You can also combine the default rules with custom rules with the `-R` option
along with one or more `-r` options.

### Including rules with tags

Each rule has an associated set of one or more tags. Use the `-T` option to view
the list of tags for each available rule.

You can then use the `-t` option to specify a tag and include the associated
rules in the lint run. For example, the following `ansible-lint` command applies
only the rules associated with the _idempotency_ tag:

```console exec="1" source="console" returncode="0"
$ ansible-lint -t idempotency playbook.yml
```

The following shows the available tags in an example set of rules and the rules
associated with each tag:

```bash exec="1" source="console"
ansible-lint -T 2>/dev/null
```

### Excluding rules with tags

To exclude rules by identifiers or tags, use the `-x SKIP_LIST` option. For
example, the following command applies all rules except those with the
_formatting_ and _metadata_ tags:

```bash
$ ansible-lint -x formatting,metadata playbook.yml
```

### Ignoring rules

To only warn about rules, use the `-w WARN_LIST` option. For example, the
following command displays only warns about violations with rules associated
with the `experimental` tag:

```console
$ ansible-lint -w experimental playbook.yml
```

By default, the `WARN_LIST` includes the `['experimental']` tag. If you define a
custom `WARN_LIST` you must add `'experimental'` so that Ansible-lint does not
fail against experimental rules.

## Muting warnings to avoid false positives

Not all linting rules are precise, some are general rules of thumb. Advanced
_git_, _yum_ or _apt_ usage, for example, can be difficult to achieve in a
playbook. In cases like this, Ansible-lint can incorrectly trigger rule
violations.

To disable rule violations for specific tasks, and mute false positives, add
`# noqa: [rule_id]` to the end of the line. It is best practice to add a comment
that explains why rules are disabled.

You can add the `# noqa: [rule_id]` comment to the end of any line in a task.
You can also skip multiple rules with a space-separated list.

```yaml
- name: This task would typically fire git-latest and partial-become rules
  become_user: alice # noqa: git-latest partial-become
  ansible.builtin.git: src=/path/to/git/repo dest=checkout
```

If the rule is line-based, `# noqa: [rule_id]` must be at the end of the line.

```yaml
- name: This would typically fire jinja[spacing]
  get_url:
    url: http://example.com/file.conf
    dest: "{{dest_proj_path}}/foo.conf" # noqa: jinja[spacing]
```

If you want Ansible-lint to skip a rule entirely, use the `-x` command line
argument or add it to `skip_list` in your configuration.

The least preferred method of skipping rules is to skip all task-based rules for
a task, which does not skip line-based rules. You can use the
`skip_ansible_lint` tag with all tasks or the `warn` parameter with the
_command_ or _shell_ modules, for example:

```yaml
- name: This would typically fire no-free-form
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

## Applying profiles

Ansible-lint profiles allow content creators to progressively improve the
quality of Ansible playbooks, roles, and collections.

During early development cycles, you need Ansible-lint rules to be less strict.
Starting with the minimal profile ensures that Ansible can load your content. As
you move to the next stage of developing content, you can gradually apply
profiles to avoid common pitfalls and brittle complexity. Then, when you are
ready to publish or share your content, you can use the `shared` and
`production` profiles with much stricter rules. These profiles harden security,
guarantee reliability, and ensure your Ansible content is easy for others to
contribute to and use.

!!! note

    Tags such as `opt-in` and `experimental` do not take effect for rules that are included in profiles, directly or indirectly.
    If a rule is in a profile, Ansible-lint applies that rule to the content.

After you install and configure `ansible-lint`, you can apply profiles as
follows:

1. View available profiles with the `--list-profiles` flag.

   ```bash
   ansible-lint --list-profiles
   ```

2. Specify a profile with the `--profile` parameter to lint your content with
   those rules, for example:

- Enforce standard styles and formatting with the `basic` profile.

  ```bash
  ansible-lint --profile=basic
  ```

- Ensure automation consistency, reliability, and security with the `safety`
  profile.

  ```bash
  ansible-lint --profile=safety
  ```

[code climate]:
  https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#data-types
[sarif]:
  https://docs.oasis-open.org/sarif/sarif/v2.1.0/csprd01/sarif-v2.1.0-csprd01.html
