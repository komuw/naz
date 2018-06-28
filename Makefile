upload:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf naz.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/* -r testpypi
	@pip install -U -i https://testpypi.python.org/pypi naz

uploadprod:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf naz.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/*
	@pip install -U naz

# you can run single testcase as;
# python -m unittest -v tests.test_client.TestClient.test_can_connect
test:
	@printf "\n removing pyc files::\n" && find . -name '*.pyc' -delete;find . -name '__pycache__' -delete | echo
	@printf "\n coverage erase::\n" && coverage erase
	@printf "\n coverage run::\n" && coverage run --omit="*tests*,*.virtualenvs/*,*.venv/*,*__init__*" -m unittest discover -v -s .
	@printf "\n coverage report::\n" && coverage report --show-missing --fail-under=70
	@printf "\n run flake8::\n" && flake8 .
	@printf "\n run pylint::\n" && pylint --enable=E --disable=W,R,C --unsafe-load-any-extension=y example/ naz/ tests/