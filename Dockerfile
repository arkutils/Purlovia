FROM python:3.7-slim-buster

ARG COMMIT=""
ARG BRANCH=dev

ENV COMMIT_SHA $COMMIT
ENV COMMIT_BRANCH $BRANCH

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# Maybe???
ENV PYTHONDONTWRITEBYTECODE 1

# Install:
#  git for output repo management
#  ssh for git to use contacting GitHub
#  lib32gcc1 as required by SteamCMD
#
# Clean up caches
# Create /app path and a safe user
RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends -y git openssh-client lib32gcc1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/log/* \
    && mkdir -p /app \
    && groupadd -r purlovia \
    && useradd --no-log-init -r -g purlovia -d /app purlovia

# Copy the app over
WORKDIR /app
COPY . .

# Install:
#  gcc for library compilation
#  requirements from Pipfile.lock using pipenv, system-wide
#
# Compile the version-grabbing log hook
# Uninstall gcc and clean up caches
RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends -y gcc libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/log/* \
    && pip3 install pipenv \
    && pipenv install --deploy --system \
    && pip3 uninstall -y pipenv \
    && gcc /app/utils/shootergameserver_fwrite_hook.c -o /app/utils/shootergameserver_fwrite_hook.so -fPIC -shared -ldl \
    && apt-get purge -y --auto-remove gcc libc6-dev \
    && rm -r /root/.cache \
    && rm Pipfile Pipfile.lock


VOLUME /app/logs /app/livedata /app/output /app/config

USER purlovia:purlovia
CMD [ "python3", "-m", "automate"]
