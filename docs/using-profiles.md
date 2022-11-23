(using-lint-profiles)=

# Applying profiles

Ansible-lint profiles allow content creators to progressively improve the quality of Ansible playbooks, roles, and collections.

During early development cycles, you need Ansible-lint rules to be less strict.
Starting with the minimal profile ensures that Ansible can load your content.
As you move to the next stage of developing content, you can gradually apply profiles to avoid common pitfalls and brittle complexity.
Then, when you are ready to publish or share your content, you can use the `shared` and `production` profiles with much stricter rules.
These profiles harden security, guarantee reliability, and ensure your Ansible content is easy for others to contribute to and use.

```{note}
Tags such as `opt-in` and `experimental` do not take effect for rules that are included in profiles, directly or indirectly.
If a rule is in a profile, Ansible-lint applies that rule to the content.
```

After you install and configure `ansible-lint`, you can apply profiles as follows:

1. View available profiles with the `--list-profiles` flag.

   ```bash
   ansible-lint --list-profiles
   ```

2. Specify a profile with the `--profile` parameter to lint your content with those rules, for example:

- Enforce standard styles and formatting with the `basic` profile.

  ```bash
  ansible-lint --profile=basic
  ```

- Ensure automation consistency, reliability, and security with the `safety` profile.

  ```bash
  ansible-lint --profile=safety
  ```

```{toctree}
:maxdepth: 1

profiles
```
