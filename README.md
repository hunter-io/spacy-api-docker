# spaCy API with Docker

This repository is a derived work of [jgontrum/spacy-api-docker](https://github.com/jgontrum/spacy-api-docker) with some changes:

* It loads the `en_core_web_lg` model instead of the default `en_core_web_sm` one
* It uses gunicorn for improved CPU usage. Use the `WORKERS` environement variable to change the default of 4 workds. Keep in mind though that each worker uses a large amount of RAM.

## Usage

`docker run -p "3000:80" quay.io/hunter-io/spacy-api:2`

Go to https://github.com/jgontrum/spacy-api-docker#rest-api-documentation for the documentation.
