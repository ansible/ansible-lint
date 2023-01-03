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

License:        GPL-3.0-or-later AND MIT
URL:            https://github.com/ansible/ansible-lint
Source0:        %{pypi_source}

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
%if %{with check}
# These are required for tests:
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-pytest-xdist
BuildRequires:  python%{python3_pkgversion}-libselinux
BuildRequires:  git-core
%endif
Requires:       git-core


%description
Ansible-lint checks ansible content for practices and behaviors that could
potentially be improved.

%prep
%autosetup


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files ansiblelint


%check
# Don't try to import tests that import pytest which isn't available at runtime
%pyproject_check_import -e 'ansiblelint.testing*' -e 'ansiblelint.rules.conftest'
%if %{with check}
%pytest \
  -v \
  --disable-pytest-warnings \
  --numprocesses=auto \
%if %{with privileged_tests}
  tests
%else
  tests/unit
%endif
%endif


%files -f %{pyproject_files}
%{_bindir}/ansible-lint
%license COPYING docs/licenses/LICENSE.mit.txt
%doc docs/ README.md

%changelog
