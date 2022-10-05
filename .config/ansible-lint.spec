# spell-checker:ignore bcond pkgversion buildrequires autosetup PYTHONPATH noarch buildroot bindir sitelib numprocesses clib
# All tests require Internet access
# to test in mock use:  --enable-network --with check
# to test in a privileged environment use:
#   --with check --with privileged_tests
%bcond_with     check
%bcond_with     privileged_tests

Name:           ansible-lint
Version:        VERSION_PLACEHOLDER
Release:        1%{?dist}
Summary:        Ansible-lint checks ansible content for common mistakes

License:        MIT
URL:            https://github.com/ansible-community/ansible-lint
Source0:        %{pypi_source}

BuildArch:      noarch

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python%{python3_pkgversion}-build
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-pip
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-setuptools_scm
BuildRequires:  python%{python3_pkgversion}-wheel
%if %{with check}
# These are required for tests:
BuildRequires:  python%{python3_pkgversion}-pyyaml
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-pytest-xdist
BuildRequires:  python%{python3_pkgversion}-libselinux
BuildRequires:  git
%endif
# Named based on fedora 35:
Requires:       ansible-core >= 2.12.0
Requires:       python3-packaging
Requires:       python3-pyyaml
Requires:       python3-rich
Requires:       python3-ruamel-yaml
Requires:       python3-ruamel-yaml-clib
Requires:       python3-wcmatch
Requires:       yamllint

# generate_buildrequires
# pyproject_buildrequires

%description
Ansible-lint checks ansible content for practices and behaviors that could
potentially be improved.

%prep
%autosetup


%build
%pyproject_wheel


%install
%pyproject_install


%if %{with check}
%check
PYTHONPATH=%{buildroot}%{python3_sitelib} \
  pytest-3 \
  -v \
  --disable-pytest-warnings \
  --numprocesses=auto \
%if %{with privileged_tests}
  tests
%else
  tests/unit
%endif
%endif


%files
%{python3_sitelib}/ansiblelint/
%{python3_sitelib}/ansible_lint-*.dist-info/
%{_bindir}/ansible-lint
%license COPYING
%doc docs/* README.md

%changelog
Available at https://github.com/ansible-community/ansible-lint/releases
