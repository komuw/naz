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

# to find types, use reveal_type eg: reveal_type(asyncio.get_event_loop())
# see: http://mypy.readthedocs.io/en/latest/common_issues.html#displaying-the-type-of-an-expression
test:
	@export PYTHONASYNCIODEBUG='2'
	@printf "\n removing pyc files::\n" && find . -name '*.pyc' -delete;find . -name '__pycache__' -delete | echo
	@printf "\n coverage erase::\n" && coverage erase
	@printf "\n coverage run::\n" && coverage run --omit="*tests*,*.virtualenvs/*,*virtualenv/*,*.venv/*,*__init__*" -m unittest discover -v -s .
	@printf "\n coverage report::\n" && coverage report --show-missing --fail-under=84
	@printf "\n coverage report html::\n" && coverage html --fail-under=86 --title=naz_coverage
	@printf "\n run flake8::\n" && flake8 .
	@printf "\n run pylint::\n" && pylint --enable=E --disable=W,R,C --unsafe-load-any-extension=y examples/ naz/ tests/ cli/
	@printf "\n run bandit::\n" && bandit -r --exclude .venv -ll .
	@printf "\n run mypy::\n" && mypy --show-column-numbers -m naz.q -m naz.throttle -m naz.ratelimiter -m naz.hooks -m naz.sequence


asciinema rec --idle-time-limit 2 first.cast
asciinema play -i 2 docs/first.cast
asciinema play -i 2 -s 2 docs/first.cast


---
#### 1.2.1 codeee
![codeee](docs/2times.png)                  
  

---
#### 1.2.2 codee2
![codeee](docs/1times.png)    


---
![codeee](docs/2times.png) {this is what we will do}                  
  

---
![codeee](docs/1times.png)    


Use https://carbon.now.sh for code png's


