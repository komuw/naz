upload:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf naz.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/* -r testpypi
	@pip install -U -i https://testpypi.python.org/pypi naz


VERSION_STRING=$$(cat naz/__version__.py | grep "__version__" | sed -e 's/"__version__"://' | sed -e 's/,//g' | sed -e 's/"//g' | sed -e 's/ //g')
uploadprod:
	@printf "\n building sphinx documentation \n" && sphinx-build -a -E documentation/sphinx-docs/ docs/
	@printf "\n git commit docs/ \n" && git add docs/ && git commit -m 'update docs/' | echo
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf naz.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/*
	@printf "\n creating git tag: $(VERSION_STRING) \n"
	@printf "\n with commit message, see Changelong: https://github.com/komuw/naz/blob/master/CHANGELOG.md \n" && git tag -a "$(VERSION_STRING)" -m "see Changelong: https://github.com/komuw/naz/blob/master/CHANGELOG.md"
	@printf "\n git push the tag::\n" && git push --all -u --follow-tags
	@pip install -U naz

# you can run single testcase as;
# python -m unittest -v tests.test_client.TestClient.test_can_connect

# to find types, use reveal_type eg: reveal_type(asyncio.get_event_loop())
# see: http://mypy.readthedocs.io/en/latest/common_issues.html#displaying-the-type-of-an-expression
test:
	@export PYTHONASYNCIODEBUG='2'
	@printf "\n removing pyc files::\n" && find . -name '*.pyc' -delete;find . -name '__pycache__' -delete | xargs echo
	@printf "\n coverage erase::\n" && coverage erase
	@printf "\n coverage run::\n" && coverage run --omit="*tests*,*examples/*,*.virtualenvs/*,*virtualenv/*,*.venv/*,*__init__*" -m unittest discover -v -s .
	@printf "\n coverage report::\n" && coverage report --show-missing --fail-under=84
	@printf "\n coverage report html::\n" && coverage html --fail-under=84 --title=naz_coverage
	@printf "\n run flake8::\n" && flake8 .
	@printf "\n run pylint::\n" && pylint --enable=E --disable=W,R,C naz/ tests/ cli/ documentation/ examples/ benchmarks/
	@printf "\n run bandit::\n" && bandit -r --exclude .venv -ll .
	@printf "\n run mypy::\n" && mypy --show-column-numbers --ignore-missing-imports -p cli -p naz
	@printf "\n run pytype::\n" && pytype --verbosity 0 --python-version 3.6 --protocols --strict-import --keep-going naz/ cli/

# note `.nojekyll` file is important inside `docs/` folder
# without it, css styling for docs in https://komuw.github.io/naz/ is broken
sphinx:
	@touch docs/.nojekyll
	@sphinx-build -a -E documentation/sphinx-docs/ docs/
