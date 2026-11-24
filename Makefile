.PHONY: check demo
check:
	python -m unittest discover -s tests -v
	$(MAKE) -C labs/routing-audit demo
	python demo/eval.py
	python labs/eval-gate/run.py
	python -m unittest discover -s labs/eval-gate -v
	python labs/workbook-eval/workbook_eval.py
	python -m unittest discover -s labs/workbook-eval -v
	python demo/quality_gate.py
demo: check
