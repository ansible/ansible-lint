The reason that every roles test gets its own directory is that while they
use the same three roles, the way the tests work makes sure that when the
second one runs, the roles and their local plugins from the first test are
still known to Ansible. For that reason, their names reflect the directory
they are in to make sure that tests don't use modules/plugins found by
other tests.
