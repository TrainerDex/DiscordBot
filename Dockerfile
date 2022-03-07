FROM python:3.10-slim

RUN apt-get update && apt-get install -y git
RUN pip install -U pipenv virtualenv

WORKDIR /opt/trainerdex

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy

COPY . .

CMD [ "pipenv", "run", "python", "run.py" ]