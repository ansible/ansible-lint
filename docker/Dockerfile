FROM python:3.7-alpine3.9

ENV ANSIBLE_LINT_VERSION=4.1.0

RUN set -xe \
    && apk add --no-cache --progress --virtual .build-deps gcc musl-dev libffi-dev openssl-dev make \
    \
    && pip install ansible-lint==${ANSIBLE_LINT_VERSION} \
    \
    && echo "****** Remove unused system librabies ******" \
    && apk del --progress .build-deps

ENTRYPOINT ["ansible-lint"]
