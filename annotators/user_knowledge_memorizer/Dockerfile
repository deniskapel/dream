FROM python:3.9.1

WORKDIR /src

ARG SERVICE_PORT
ARG SRC_DIR
ARG TERMINUSDB_SERVER_PASSWORD
ARG TERMINUSDB_SERVER_URL
ARG TERMINUSDB_SERVER_TEAM
ARG TERMINUSDB_SERVER_DB
ARG CONFIG

ENV SERVICE_PORT=$SERVICE_PORT
ENV TERMINUSDB_SERVER_PASSWORD=$TERMINUSDB_SERVER_PASSWORD
ENV TERMINUSDB_SERVER_URL=$TERMINUSDB_SERVER_URL
ENV TERMINUSDB_SERVER_TEAM=$TERMINUSDB_SERVER_TEAM
ENV TERMINUSDB_SERVER_DB=$TERMINUSDB_SERVER_DB
ENV CONFIG=$CONFIG

RUN pip install -U pip wheel setuptools

COPY ./annotators/user_knowledge_memorizer/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache -r /src/requirements.txt && \
    python -m nltk.downloader wordnet && \
    pip install git+https://github.com/deeppavlov/custom_kg_svc.git@724513b4
    
COPY $SRC_DIR .


CMD gunicorn --workers=1 server:app -b 0.0.0.0:$SERVICE_PORT
