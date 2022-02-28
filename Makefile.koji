PACKAGE=acron
SPECFILE = $(PACKAGE).spec
VERSION=$(shell grep -s '^Version' $(SPECFILE) | sed -e 's/Version: *//')
PKGNAME=$(PACKAGE)-$(VERSION)
TARFILE=python3-$(PKGNAME).tgz
OWNER=acron-devs
DIST ?= $(shell rpm --eval %{dist})

all: sources

sources:
	sed -e "s/version=.*/version=\'${VERSION}\',/" python/setup.py > python/setup.py.new
	mv python/setup.py.new python/setup.py
	tar -czf $(TARFILE) ./etc ./man ./python ./selinux ./usr ./var COPYING COPYRIGHT LICENSE

scratch:
	koji build acron7 --nowait --scratch  git+ssh://git@gitlab.cern.ch:7999/$(OWNER)/$(PACKAGE).git#$(shell git rev-parse HEAD)

build:
	koji build acron7 --nowait git+ssh://git@gitlab.cern.ch:7999/$(OWNER)/$(PACKAGE).git#$(shell git rev-parse HEAD)

rpm:	sources
	rpmbuild  --define 'dist $(DIST)' --define "_topdir $(PWD)/build" --define "_sourcedir ${PWD}" -ba $(SPECFILE)

srpm:	sources
	rpmbuild  --define 'dist $(DIST)' --define "_topdir $(PWD)/build" --define "_sourcedir ${PWD}" -bs $(SPECFILE)
