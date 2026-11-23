.PHONY: check demo
check:
	python -m unittest discover -s tests -v
	$(MAKE) -C labs/routing-audit demo
	python demo/eval.py
	python labs/eval-gate/run.py
	python -m unittest discover -s labs/eval-gate -v
	python demo/quality_gate.py
demo: check
