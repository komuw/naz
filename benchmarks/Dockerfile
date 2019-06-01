FROM python:3.7

WORKDIR /usr/src/app
COPY ./ /usr/src/app

ENV PYTHONPATH="/usr/src/app"

RUN find . -name '*.pyc' -delete;find . -name '__pycache__' -delete;find . -name '*.pid' -delete
RUN pip install -r requirements/base.txt
