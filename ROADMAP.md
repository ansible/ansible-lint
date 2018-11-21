# 4.0.0 (Target Release Date: 07-Dec-2018)

* Packaging: consistency and automation #389
* Additional default rules for ansible-lint #384
* Extend test module so unittests can use runner on text snippets for roles and playbooks, keeping rule unittest in one file, fix double sudo rule output #393
* Fix running with role path containing single or multiple dirs #390
* Add doc site #394
* Updated rule TrailingWhitespaceRule.py to remove carriage return char #323
* Add Package has retry rule #324
* Allow snake_case module names for rules #82
* Add a severity property to the default rules #379
* GitHub repository edits: move to ansible org, add CODE_OF_CONDUCT, add ROADMAP, edit labels

# 4.1.0

* Lint all yaml in tasks/ and handlers/ regardless of import or include #373
* Check for file or directory presence #378
* Add `matchvar` method to lint vars in vars.yml #354
* Add support for include_tasks which currently are skipped #362
* Skip specific rule(s) for a specific task #364
* Consider adopting/absorbing ansible-lint-junit #396

See progress here: https://github.com/ansible/ansible-lint/milestones
