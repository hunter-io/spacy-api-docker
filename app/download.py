import os
import json

from spacy.cli import download

print("Starting download")

lang = "en_core_web_lg"
download(model=lang, direct=False)

print("Done!")
