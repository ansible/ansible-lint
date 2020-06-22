---
name: 🐛 Bug report
about: Create a bug report. Please test against the master branch before submitting it.
labels: priority/medium, status/new, type/bug
---
<!--- Verify first that your issue is not already reported on GitHub -->
<!--- Also test if the latest release and master branch are affected too -->

##### Summary
<!--- Explain the problem briefly below -->


##### Issue Type

- Bug Report

##### Ansible and Ansible Lint details
<!--- Paste verbatim output between tripple backticks -->
```console (paste below)
ansible --version

ansible-lint --version

```

- ansible installation method: one of source, pip, OS package
- ansible-lint installation method: one of source, pip, OS package

##### OS / ENVIRONMENT
<!--- Provide all relevant information below, e.g. target OS versions, network device firmware, etc. -->


##### STEPS TO REPRODUCE
<!--- Describe exactly how to reproduce the problem, using a minimal test-case -->

<!--- Paste example playbooks or commands between tripple backticks below -->
```console (paste below)

```

<!--- HINT: You can paste gist.github.com links for larger files -->

##### Desired Behaviour
<!--- Describe what you expected to happen when running the steps above -->

Possible security bugs should be reported via email to `security@ansible.com`

##### Actual Behaviour
<!--- Describe what actually happened. If possible run with extra verbosity (-vvvv) -->

Please give some details of what is actually happening.
Include a [minimum complete verifiable example] with:
- playbook
- output of running ansible-lint
- if you're getting a stack trace, output of
  `ansible-playbook --syntax-check playbook`


<!--- Paste verbatim command output between tripple backticks -->
```paste below

```


[minimum complete verifiable example]: http://stackoverflow.com/help/mcve
