# Maintainer: Amin Vakil <info AT aminvakil DOT com>
# Contributor: Jelle van der Waa <jelle@archlinux.org>
# Contributor: Frederik Schwan <freswa at archlinux dot org>
# Contributor: Sander Boom <sanderboom@gmail.com>

_pkgname=ansible-lint
pkgname=ansible-lint-test
pkgver=5.0.8.dev86
pkgrel=1
pkgdesc="Checks playbooks for practices and behaviour that could potentially be improved."
arch=('any')
url="https://github.com/ansible-community/ansible-lint"
license=('MIT')
depends=('python' 'python-ruamel-yaml' 'python-pyaml' 'python-rich' 'python-packaging'
          'python-wcmatch' 'python-enrich' 'python-tenacity' 'ansible-core')
makedepends=('python-setuptools' 'python-setuptools-scm' 'python-toml')
optdepends=('yamllint: check for yaml syntax mistakes' 'ansible: check playbooks'
            'ansible: check official ansible collections')
provides=('ansible-lint')
conflicts=('ansible-lint')

pkgver() {
  cd ..
  # Get the version number.
  python setup.py --version
}

build() {
  cd ..
  python setup.py build
}

package() {
  cd ..
  PYTHONHASHSEED=0 python setup.py install --root="${pkgdir}" --optimize=1
  install -Dm 644 LICENSE -t "${pkgdir}"/usr/share/licenses/${pkgname}
}
