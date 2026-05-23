FROM python:3.12-alpine3.20
LABEL maintainer="PouyaKhajaviDev"

ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV="/venv"
ENV PATH="/venv/bin:$PATH"
ENV PIP_INDEX_URL="https://package-mirror.liara.ir/repository/pypi/simple"


COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./ecommerce_api /app

WORKDIR /app
EXPOSE 8000


ARG DEV=false

RUN echo "https://mirror.arvancloud.ir/alpine/v3.20/main" > /etc/apk/repositories && \
    echo "https://mirror.arvancloud.ir/alpine/v3.20/community" >> /etc/apk/repositories && \
    apk add --no-cache libpq && \
    apk add --no-cache --virtual .build-deps \
        gcc python3-dev musl-dev postgresql-dev && \
    python -m venv /venv && \
    export PIP_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /venv/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .build-deps && \
    adduser --disabled-password --no-create-home django-user


ENV VIRTUAL_ENV="/venv"
ENV PATH="/venv/bin:$PATH"
ENV PIP_INDEX_URL="https://package-mirror.liara.ir/repository/pypi/simple"

USER django-user