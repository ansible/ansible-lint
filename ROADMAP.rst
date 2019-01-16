4.1.0
=====

- Skip specific rule(s) for a specific task #364
- Lint all yaml in tasks/ and handlers/ regardless of import or include #373
- New rule on using pipefail #442, #199
- Remove rule 405 checking for retry on package modules #456

4.2.0
=====

- Check for file or directory presence #378
- Add `matchvar` method to lint vars in vars.yml #354
- Add support for include_tasks which currently are skipped #362
- Consider adopting/absorbing ansible-lint-junit #396

See progress here: https://github.com/ansible/ansible-lint/milestones
