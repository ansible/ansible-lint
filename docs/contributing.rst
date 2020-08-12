.. include:: ../.github/CONTRIBUTING.rst
   :end-before: DO-NOT-REMOVE-deps-snippet-PLACEHOLDER

Module dependency graph
-----------------------

Extra care should be taken when considering adding any dependency. Removing
most dependencies on Ansible internals is desired as these can change
without any warning.

.. command-output:: pipdeptree -p ansible-lint

.. include:: ../.github/CONTRIBUTING.rst
   :start-after: DO-NOT-REMOVE-deps-snippet-PLACEHOLDER

Adding a new rule
-----------------

Writing a new rule became easier as we now allow you to include
**implementation, testing and documentation** in a single rule file.

One good example is MetaTagValidRule_ which can easily be copied in order
to create a new rule by following the steps below:

* Install test dependencies using ``pip install ansible-lint[test]``
* Use a short by clear class name, which must match the filename
* Pick an unused ``id``, the first number is used to determine its category,
  see which one fits best.
* Update all class level variables
* Implement linting methods needed by you. Feel free to look on how similar
  rules were implemented.
* Update the tests. It must have at least one test and likely also a negative
  match one. If the rule is task specific, you may want to test its use inside
  blocks as well.
* Run the rule file ``python NewRule.py`` as this will run tests unique to that
  rule.
* Now run ``tox`` in order to run all ansible-lint tests. Adding a new rule can
  break some other tests. Update them if needed.
* Run ``ansible-lint -L`` and check that the rule description renders nicely
  and correct.
* Build the docs using ``tox -e docs`` and check that the new rule is displayed
  correctly in them.
* Assure linting is passing with ``tox -e lint``.
* Make a commit that explains why the rule is added and that eventually
  closing an existing bug by including ``Fixes: #123`` in its description.
  Commit message should follow the 50/72 formatting rule.
* Open a draft pull-request. When CI/CD reports green, move the draft PR from
  draft to ready for review.

.. _MetaTagValidRule: https://github.com/ansible/ansible-lint/blob/master/lib/ansiblelint/rules/MetaTagValidRule.py
