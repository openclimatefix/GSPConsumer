FROM python:3.12-slim

ARG TESTING=0

# make sure it doesnt fail if the docker file doesnt know the git commit
ARG GIT_PYTHON_REFRESH=quiet

RUN apt-get update && apt-get install -y git

# copy files
COPY setup.py app/setup.py
COPY README.md app/README.md
COPY requirements.txt app/requirements.txt

# install requirements
RUN pip install -r app/requirements.txt
Run pip install git+https://github.com/SheffieldSolar/PV_Live-API#pvlive_api

# copy library files
COPY gspconsumer/ app/gspconsumer/
COPY tests/ app/tests/

# change to app folder
WORKDIR /app

# install library
RUN pip install -e .

RUN if [ "$TESTING" = 1 ]; then pip install pytest pytest-cov coverage; fi

CMD ["python", "-u","gspconsumer/app.py"]
