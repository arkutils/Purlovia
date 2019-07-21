FROM python:3.7-slim-buster

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# Maybe???
ENV PYTHONDONTWRITEBYTECODE 1

# Install:
#  git for output repo management
#  ssh for git to use contacting GitHub
#  lib32gcc1 as required by SteamCMD
RUN set -ex \
    && apt-get update && apt-get install --no-install-recommends -y git openssh-client lib32gcc1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && mkdir -p /app \
    && groupadd -r purlovia \
    && useradd --no-log-init -r -g purlovia -d /app purlovia

# Grab Pipfile and Pipfile.lock then install requirements using pipenv, system-wide
WORKDIR /app
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN set -ex \
    && pip3 install pipenv \
    && pipenv install --deploy --system \
    && pip3 uninstall -y pipenv \
    && rm Pipfile Pipfile.lock

# Copy the app over and prepare its environment
COPY . .
RUN set -ex \
    && rm Pipfile Pipfile.lock

VOLUME /app/logs /app/livedata /app/output /app/config

USER purlovia:purlovia
CMD [ "python3", "-m", "automate"]
