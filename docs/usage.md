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

[annotation]: https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#setting-an-error-message
[github actions]: https://github.com/features/actions
