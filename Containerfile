FROM registry.fedoraproject.org/fedora:latest

WORKDIR /root
RUN <<EOF
dnf install python3-pip git -y
python3 -m pip install ansible-lint==24.2.3
git clone  https://github.com/anshulbehl/ilo-ansible-collection
EOF

ENV ANSIBLE_LINT_NODEPS=1

WORKDIR /root/ilo-ansible-collection
