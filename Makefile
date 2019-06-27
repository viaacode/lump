.PHONY: docs test clean gh-pages apidocs

test:
	pytest --cov=src --cov-report html:docs/extra/coverage tests/ --doctest-modules src --verbose
	pycodestyle --max-line-length=120 src tests

docs: apidocs
	cd docs/ && make clean html

clean:
	cd docs/ && make clean

apidocs:
	sphinx-apidoc -f -e -o docs/modules/ src/lump/ && rm docs/modules/modules.rst
