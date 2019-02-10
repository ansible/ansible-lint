FROM python:2.7-slim

LABEL "maintainer"="stoe <stefan@stoelzle.me>"
LABEL "repository"="https://github.com/stoe/actions"
LABEL "homepage"="https://github.com/stoe/actions"
LABEL "version"="1.0.0"

LABEL "com.github.actions.name"="ansible-lint"
LABEL "com.github.actions.description"="Run Ansible Lint"
LABEL "com.github.actions.icon"="activity"
LABEL "com.github.actions.color"="gray-dark"

RUN pip install ansible-lint

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
