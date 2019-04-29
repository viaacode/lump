.PHONY: docs test clean gh-pages apidocs

test:
	pytest --cov=src --cov-report html tests/ --doctest-modules --verbose
	pycodestyle --max-line-length=120 src tests

docs: apidocs
	cd docs/ && make clean html

clean:
	cd docs/ && make clean

gh-pages: docs
	TMPDIR=`mktemp -d` || exit 1; \
	trap 'rm -rf "$$TMPDIR"' EXIT; \
	echo $$TMPDIR; \
	GITORIGIN=$(shell git remote get-url origin); \
	git clone "$$GITORIGIN" -b gh-pages --single-branch "$$TMPDIR"; \
	rm -r "$$TMPDIR/"*; \
	echo "lump.mikesmith.eu" > "$$TMPDIR/CNAME"; \
	cp -r docs/build/html/ "$$TMPDIR"; \
	cd "$$TMPDIR" ;\
	git add -A && git commit -a -m 'update docs' && git push --set-upstream origin gh-pages

apidocs:
	sphinx-apidoc -f -e -o docs/modules/ src/lump/ && rm docs/modules/modules.rst
