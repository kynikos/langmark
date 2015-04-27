BASEDIR=$(CURDIR)

LANGMARK=$(BASEDIR)/langmark_.py
TESTDIR=$(BASEDIR)/tests/

.PHONY: help
help:
	@echo 'make test            run the tests'

.PHONY: test
test:
	$(LANGMARK) html $(TESTDIR)test.lm > $(TESTDIR)test.html
