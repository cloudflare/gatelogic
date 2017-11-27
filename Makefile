
VIRTUALENV       ?= virtualenv
PWD              := $(shell pwd)
VENV_DIR         ?= $(PWD)/venv

RUNNOSE := ./venv/bin/nosetests -s --with-coverage --with-doctest --cover-package=gatelogic --cover-erase

.PHONY: test tests
tests: test
test: deps $(VENV_DIR)/.ok
	$(RUNNOSE)

.PHONY: deps
deps:
	@python --version 2> /dev/null
	@$(VIRTUALENV) --help > /dev/null
	dpkg -L python-dev 2> /dev/null > /dev/null

$(VENV_DIR)/.ok:
	rm -rf $(VENV_DIR)
	$(VIRTUALENV) $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --download-cache .pipcache \
		-r requirements.txt -r requirements-dev.txt
	$(VENV_DIR)/bin/python setup.py develop
	touch $(VENV_DIR)/.ok

.PHONY: clean
clean:
	rm -rf $(VENV_DIR) *.egg-info dist gatelogic*.deb \
		gatelogic/*.pyc test/*.pyc .pipcache
