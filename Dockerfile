FROM python:3.6-alpine

WORKDIR /app
ENV HOME /app

# Install the required packages
RUN apk update
RUN apk add ca-certificates curl build-base

RUN pip3 install --upgrade pip
RUN pip3 install falcon spacy falcon requests pathlib
RUN pip3 install gunicorn

ADD app/ /app

ENV languages "en_core_web_lg"
RUN python3 /app/download.py

EXPOSE 80
ENV WORKERS 4
CMD gunicorn -w $WORKERS -b 0.0.0.0:80 --max-requests 50000 --timeout 90 main:app
