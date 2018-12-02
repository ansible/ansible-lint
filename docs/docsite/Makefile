OS := $(shell uname -s)
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"):
ifeq ($(shell echo $(OS) | egrep -ic 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
CPUS ?= $(shell sysctl hw.ncpu|awk '{print $$2}')
else
CPUS ?= $(shell nproc)
endif

# Sets the build output directory if it's not already specified
ifndef BUILDDIR
	BUILDDIR = _build
endif

MODULE_ARGS=
ifdef MODULES
	MODULE_ARGS = -l $(MODULES)
endif

PLUGIN_ARGS=
ifdef PLUGINS
	PLUGIN_ARGS = -l $(PLUGINS)
endif

DOC_PLUGINS ?= cache callback connection inventory lookup shell strategy vars

assertrst:
ifndef rst
	$(error specify document or pattern with rst=somefile.rst)
endif

all: docs

docs: clean htmldocs

generate_rst: staticmin

htmldocs: generate_rst
	cd ../../lib/ansiblelint; python ./generate_docs.py
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx html

singlehtmldocs: generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx singlehtml

webdocs: docs

#TODO: leaving htmlout removal for those having older versions, should eventually be removed also
clean:
	@echo "Cleaning $(BUILDDIR)"
	-rm -rf $(BUILDDIR)/doctrees
	-rm -rf $(BUILDDIR)/html
	-rm -rf htmlout
	-rm -rf module_docs
	-rm -rf _build
	-rm -f .buildinfo
	-rm -f objects.inv
	-rm -rf *.doctrees
	@echo "Cleaning up minified css files"
	find . -type f -name "*.min.css" -delete
	@echo "Cleaning up byte compiled python stuff"
	find . -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up generated rst"

.PHONY: docs clean

staticmin:
	cat _themes/srtd/static/css/theme.css | sed -e 's/^[ 	]*//g; s/[ 	]*$$//g; s/\([:{;,]\) /\1/g; s/ {/{/g; s/\/\*.*\*\///g; /^$$/d' | sed -e :a -e '$$!N; s/\n\(.\)/\1/; ta' > _themes/srtd/static/css/theme.min.css

epub:
	(CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx epub)

htmlsingle: assertrst
	sphinx-build -j $(CPUS) -b html -d $(BUILDDIR)/doctrees ./rst $(BUILDDIR)/html rst/$(rst)
	@echo "Output is in $(BUILDDIR)/html/$(rst:.rst=.html)"
