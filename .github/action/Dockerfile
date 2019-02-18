FROM python:2.7-slim

LABEL "maintainer"="Ansible by Red Hat <info@ansible.com>"
LABEL "repository"="https://github.com/ansible/lint"
LABEL "homepage"="https://github.com/ansible/lint/tree/master/ansible-lint"
LABEL "version"="1.0.0"

LABEL "com.github.actions.name"="ansible-lint"
LABEL "com.github.actions.description"="Run Ansible Lint"
LABEL "com.github.actions.icon"="activity"
LABEL "com.github.actions.color"="gray-dark"

RUN pip install ansible-lint

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
