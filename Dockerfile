FROM python:3.11-slim

RUN pip install -U pip && pip install -U "requirementslib==2.3.0"

WORKDIR /opt/trainerdex

COPY Pipfile Pipfile
RUN python -c 'from requirementslib.models.pipfile import Pipfile; pf = Pipfile.load("."); pkgs = [pf.requirements]; print("\n".join([pkg.as_line() for section in pkgs for pkg in section]))' > requirements.txt
RUN pip install -U pip && pip install -r requirements.txt

COPY trainerdex trainerdex
COPY .env .env

CMD ["python", "-m", "trainerdex.discord_bot" ]