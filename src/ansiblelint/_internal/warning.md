# warning

`warning` is a special type of internal rule that is used to report generic
runtime warnings found during execution. As stated by its name, they are
not counted as errors, so they do not influence the final outcome.

- `warning[empty-playbook]` is raised when a playbook file has no content.
