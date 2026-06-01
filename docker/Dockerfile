FROM python:3.8.12-bullseye

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

RUN apt-get update && \
    apt-get -y install nano curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get -y install nodejs && \
    pip install --upgrade pip && \
    pip install pipenv && \
    rm -rf /var/lib/apt/lists/*

RUN adduser \
    --system \
    --gecos "" \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/Pipfile ./src/Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --deploy --dev --system

WORKDIR ${SANDBOX_DIR}

