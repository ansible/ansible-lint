# warning

`warning` is a special type of internal rule that is used to report generic
runtime warnings found during execution. As stated by its name, they are not
counted as errors, so they do not influence the final outcome.

- `warning[raw-non-string]` indicates that you are using
  `[raw](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/raw_module.html#ansible-collections-ansible-builtin-raw-module)`
  module with non-string arguments, which is not supported by Ansible.
