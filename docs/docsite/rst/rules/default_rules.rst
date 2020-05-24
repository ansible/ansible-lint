
.. _lint_default_rules:

Default Rules
=============

.. contents::
   :local:

Below you can see the list of default rules Ansible Lint use to evaluate playbooks and roles:



Deprecated Rules (1xx)
----------------------

.. _101:

101: Deprecated always_run
**************************

Instead of ``always_run``, use ``check_mode``

.. _102:

102: No Jinja2 in when
**********************

``when`` lines should not include Jinja2 variables

.. _103:

103: Deprecated sudo
********************

Instead of ``sudo``/``sudo_user``, use ``become``/``become_user``.

.. _104:

104: Using bare variables is deprecated
***************************************

Using bare variables is deprecated. Update your playbooks so that the environment value uses the full variable syntax ``{{ your_variable }}``

.. _105:

105: Deprecated module
**********************

These are deprecated modules, some modules are kept temporarily for backwards compatibility but usage is discouraged. For more details see: https://docs.ansible.com/ansible/latest/modules/list_of_all_modules.html

.. _106:

106: Role name {} does not match ``^[a-z][a-z0-9_]+$`` pattern
**************************************************************

Role names are now limited to contain only lowercase alphanumeric characters, plus '_' and start with an alpha character. See `developing collections <https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#roles-directory>`_

Formatting Rules (2xx)
----------------------

.. _201:

201: Trailing whitespace
************************

There should not be any trailing whitespace

.. _202:

202: Octal file permissions must contain leading zero or be a string
********************************************************************

Numeric file permissions without leading zero can behave in unexpected ways. See http://docs.ansible.com/ansible/file_module.html

.. _203:

203: Most files should not contain tabs
***************************************

Tabs can cause unexpected display issues, use spaces

.. _204:

204: Lines should be no longer than 160 chars
*********************************************

Long lines make code harder to read and code review more difficult

.. _205:

205: Use ".yml" or ".yaml" playbook extension
*********************************************

Playbooks should have the ".yml" or ".yaml" extension

.. _206:

206: Variables should have spaces before and after: {{ var_name }}
******************************************************************

Variables should have spaces before and after: ``{{ var_name }}``

Command-Shell Rules (3xx)
-------------------------

.. _301:

301: Commands should not change things if nothing needs doing
*************************************************************

Commands should either read information (and thus set ``changed_when``) or not do something if it has already been done (using creates/removes) or only do it if another check has a particular result (``when``)

.. _302:

302: Using command rather than an argument to e.g. file
*******************************************************

Executing a command when there are arguments to modules is generally a bad idea

.. _303:

303: Using command rather than module
*************************************

Executing a command when there is an Ansible module is generally a bad idea

.. _304:

304: Environment variables don't work as part of command
********************************************************

Environment variables should be passed to ``shell`` or ``command`` through environment argument

.. _305:

305: Use shell only when shell functionality is required
********************************************************

Shell should only be used when piping, redirecting or chaining commands (and Ansible would be preferred for some of those!)

.. _306:

306: Shells that use pipes should set the pipefail option
*********************************************************

Without the pipefail option set, a shell command that implements a pipeline can fail and still return 0. If any part of the pipeline other than the terminal command fails, the whole pipeline will still return 0, which may be considered a success by Ansible. Pipefail is available in the bash shell.

Module Rules (4xx)
------------------

.. _401:

401: Git checkouts must contain explicit version
************************************************

All version control checkouts must point to an explicit commit or tag, not just ``latest``

.. _402:

402: Mercurial checkouts must contain explicit revision
*******************************************************

All version control checkouts must point to an explicit commit or tag, not just ``latest``

.. _403:

403: Package installs should not use latest
*******************************************

Package installs should use ``state=present`` with or without a version

.. _404:

404: Doesn't need a relative path in role
*****************************************

``copy`` and ``template`` do not need to use relative path for ``src``

Task Rules (5xx)
----------------

.. _501:

501: become_user requires become to work as expected
****************************************************

``become_user`` without ``become`` will not actually change user

.. _502:

502: All tasks should be named
******************************

All tasks should have a distinct name for readability and for ``--start-at-task`` to work

.. _503:

503: Tasks that run when changed should likely be handlers
**********************************************************

If a task has a ``when: result.changed`` setting, it is effectively acting as a handler

.. _504:

504: Do not use 'local_action', use 'delegate_to: localhost'
************************************************************

Do not use ``local_action``, use ``delegate_to: localhost``

.. _505:

505: referenced files must exist
********************************

All files referenced by by include / import tasks must exist. The check excludes files with jinja2 templates in the filename.

Idiom Rules (6xx)
-----------------

.. _601:

601: Don't compare to literal True/False
****************************************

Use ``when: var`` rather than ``when: var == True`` (or conversely ``when: not var``)

.. _602:

602: Don't compare to empty string
**********************************

Use ``when: var|length > 0`` rather than ``when: var != ""`` (or conversely ``when: var|length == 0`` rather than ``when: var == ""``)

Metadata Rules (7xx)
--------------------

.. _701:

701: meta/main.yml should contain relevant info
***********************************************

meta/main.yml should contain: ``author, description, license, min_ansible_version, platforms``

.. _702:

702: Tags must contain lowercase letters and digits only
********************************************************

Tags must contain lowercase letters and digits only, and ``galaxy_tags`` is expected to be a list

.. _703:

703: meta/main.yml default values should be changed
***************************************************

meta/main.yml default values should be changed for: ``author, description, company, license, license``

.. _704:

704: meta/main.yml video_links should be formatted correctly
************************************************************

Items in ``video_links`` in meta/main.yml should be dictionaries, and contain only keys ``url`` and ``title``, and have a shared link from a supported provider

Core Rules (9xx)
----------------

.. _901:

901: Failed to load or parse file
*********************************

Linter failed to process a YAML file, possible not an Ansible file.
