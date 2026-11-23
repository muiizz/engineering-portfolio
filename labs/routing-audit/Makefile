PYTHON ?= python3

.PHONY: demo test

demo: test
	$(PYTHON) -B audit.py

test:
	$(PYTHON) -B -m unittest -v
