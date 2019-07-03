.PHONY: docs test clean gh-pages apidocs

test:
	pytest --cov=src --cov-report html:docs/extra/coverage tests/ --doctest-modules src --verbose
	pycodestyle --max-line-length=120 src tests

docs:
	cd docs/ && make clean html

clean:
	cd docs/ && make clean
