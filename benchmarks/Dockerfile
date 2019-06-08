FROM python:3.7

ARG NAZ_BRANCH=master

WORKDIR /usr/src/app
COPY ./ /usr/src/app

ENV PYTHONPATH="/usr/src/app"

RUN printf "\n\n\t Installing using branch: ${NAZ_BRANCH} \n\n" && \
    wget -nc https://github.com/komuw/naz/archive/${NAZ_BRANCH}.zip && \
    unzip ${NAZ_BRANCH}.zip && \
    cd naz-${NAZ_BRANCH} && \
    pip install -e .[benchmarks] && \
    cd .. && \
    rm -rf naz-${NAZ_BRANCH} && \
    rm -rf ${NAZ_BRANCH}.zip && \
    find . -name '*.pyc' -delete;find . -name '__pycache__' -delete;find . -name '*.pid' -delete
