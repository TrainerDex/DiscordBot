FROM python:3.10-slim

RUN pip install -U pipenv virtualenv

WORKDIR /opt/trainerdex

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy

COPY . .

CMD [ "pipenv", "run", "python", "-m", "trainerdex_discord_bot" ]