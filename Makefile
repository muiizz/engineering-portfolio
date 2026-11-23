.PHONY: check demo
check:
	python -m unittest discover -s tests -v
	$(MAKE) -C labs/routing-audit demo
	python demo/eval.py
	python labs/eval-gate/run.py
	python demo/quality_gate.py
demo: check
