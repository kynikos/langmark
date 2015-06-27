BASEDIR=$(CURDIR)

LANGMARK=$(BASEDIR)/langmark_.py
TESTDIR=$(BASEDIR)/tests

.PHONY: help
help:
	@echo 'make docs            make the documentation pages'
	@echo 'make test            run the tests               '

.PHONY: docs
docs:
	$(LANGMARK) html $(BASEDIR)/README.lm > $(BASEDIR)/README.html

.PHONY: test
test:
	$(LANGMARK) html $(TESTDIR)/test.lm > $(TESTDIR)/test.html
