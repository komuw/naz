FROM python:3.6

ARG NAZ_BRANCH=master

WORKDIR /usr/src/app
COPY ./ /usr/src/app

ENV PYTHONPATH="/usr/src/app"

RUN printf "\\n\\t Installing using branch: %s \\n" "${NAZ_BRANCH}" && \
    wget -nc "https://github.com/komuw/naz/archive/${NAZ_BRANCH}.zip" && \
    unzip ./*.zip && \
    (cd naz-*; pip install -e .[benchmarks]) && \
    rm -rf ./naz-* && \
    rm -rf ./*.zip && \
    find . -name '*.pyc' -delete;find . -name '__pycache__' -delete;find . -name '*.pid' -delete

RUN pip install "git+https://github.com/komuw/naz.git@${NAZ_BRANCH}"
