FROM python:3.9-buster AS python

ENV PYTHONUNBUFFERED=true

FROM python as build

COPY . /opt/build
ENV PATH="/root/.local/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python

RUN cd /opt/build \
    && rm -rf dist \
    && poetry update --no-interaction --no-ansi -vvv\
    && poetry build -f wheel --no-interaction --no-ansi -vvv

FROM python

COPY --from=build /opt/build/dist /opt/dist

RUN pip install /opt/dist/*.whl

EXPOSE 5000

CMD ["/usr/local/bin/gymcorp", "--database", "/data/app.db" ]
