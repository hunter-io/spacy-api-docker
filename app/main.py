import falcon
from pathlib import Path
import spacy
import json
import os

from spacy.symbols import ENT_TYPE, TAG, DEP
import spacy.about
import spacy.util

MODELS = os.getenv("languages", "").split()

_models = {}

def get_model(model_name):
    if model_name not in _models:
        _models[model_name] = spacy.load(model_name)
    return _models[model_name]


def get_dep_types(model):
    '''List the available dep labels in the model.'''
    labels = []
    for label_id in model.parser.moves.freqs[DEP]:
        labels.append(model.vocab.strings[label_id])
    return labels


def get_ent_types(model):
    '''List the available entity types in the model.'''
    labels = []
    for label_id in model.entity.moves.freqs[ENT_TYPE]:
        labels.append(model.vocab.strings[label_id])
    return labels


def get_pos_types(model):
    '''List the available part-of-speech tags in the model.'''
    labels = []
    for label_id in model.tagger.moves.freqs[TAG]:
        labels.append(model.vocab.strings[label_id])
    return labels


class ModelsResource(object):
    """List the available models.

    test with: curl -s localhost:8000/models
    """
    def on_get(self, req, resp):
        try:
            output = list(MODELS)
            resp.body = json.dumps(output, sort_keys=True, indent=2)
            resp.content_type = 'text/string'
            resp.append_header('Access-Control-Allow-Origin', "*")
            resp.status = falcon.HTTP_200
        except Exception:
            resp.status = falcon.HTTP_500

class VersionResource(object):
    """Return the used spacy / api version

    test with: curl -s localhost:8000/version
    """
    def on_get(self, req, resp):
        try:
            resp.body = json.dumps({
              "spacy": spacy.about.__version__
            }, sort_keys=True, indent=2)
            resp.content_type = 'text/string'
            resp.append_header('Access-Control-Allow-Origin', "*")
            resp.status = falcon.HTTP_200
        except Exception:
            resp.status = falcon.HTTP_500

class SchemaResource(object):
    """Describe the annotation scheme of a model.

    This does not appear to work with later spacy
    versions.
    """
    def on_get(self, req, resp, model_name):
        try:
            model = get_model(model_name)
            output = {
                'dep_types': get_dep_types(model),
                'ent_types': get_ent_types(model),
                'pos_types': get_pos_types(model)
            }

            resp.body = json.dumps(output, sort_keys=True, indent=2)
            resp.content_type = 'text/string'
            resp.append_header('Access-Control-Allow-Origin', "*")
            resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(
                'Schema construction failed',
                '{}'.format(e))

class DepResource(object):
    """Parse text and return displacy's expected JSON output.

    test with: curl -s localhost:8000/dep -d '{"text":"Pastafarians are smarter than people with Coca Cola bottles."}'
    """
    def on_post(self, req, resp):
        req_body = req.stream.read()
        json_data = json.loads(req_body.decode('utf8'))
        text = json_data.get('text')
        model_name = json_data.get('model', 'en')
        collapse_punctuation = json_data.get('collapse_punctuation', True)
        collapse_phrases = json_data.get('collapse_phrases', True)

        try:
            model = get_model(model_name)
            parse = Parse(model, text, collapse_punctuation, collapse_phrases)
            resp.body = json.dumps(parse.to_json(), sort_keys=True, indent=2)
            resp.content_type = 'text/string'
            resp.append_header('Access-Control-Allow-Origin', "*")
            resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(
                'Dependency parsing failed',
                '{}'.format(e))


class Parse(object):
    def __init__(self, nlp, text, collapse_punctuation, collapse_phrases):
        self.doc = nlp(text)
        if collapse_punctuation:
            spans = []
            for word in self.doc[:-1]:
                if word.is_punct:
                    continue
                if not word.nbor(1).is_punct:
                    continue
                start = word.i
                end = word.i + 1
                while end < len(self.doc) and self.doc[end].is_punct:
                    end += 1
                span = self.doc[start : end]
                spans.append(
                    (span.start_char, span.end_char, word.tag_, word.lemma_, word.ent_type_)
                )
            for span_props in spans:
                self.doc.merge(*span_props)

        if collapse_phrases:
            for np in list(self.doc.noun_chunks):
                np.merge(np.root.tag_, np.root.lemma_, np.root.ent_type_)

    def to_json(self):
        words = [{'text': w.text, 'tag': w.tag_} for w in self.doc]
        arcs = []
        for word in self.doc:
            if word.i < word.head.i:
                arcs.append(
                    {
                        'start': word.i,
                        'end': word.head.i,
                        'label': word.dep_,
                        'text': str(word),
                        'dir': 'left'
                    })
            elif word.i > word.head.i:
                arcs.append(
                    {
                        'start': word.head.i,
                        'end': word.i,
                        'label': word.dep_,
                        'text': str(word),
                        'dir': 'right'
                    })
        return {'words': words, 'arcs': arcs}


class Entities(object):
    def __init__(self, nlp, text):
        self.doc = nlp(text)
     
    def to_json(self):
        return [
            {
            'start': ent.start_char,
            'end': ent.end_char,
            'type': ent.label_,
            'text': str(ent)
            } for ent in self.doc.ents
        ]

class EntResource(object):
    """Parse text and return displaCy ent's expected output."""
    def on_post(self, req, resp):
        req_body = req.stream.read()
        json_data = json.loads(req_body.decode('utf8'))
        text = json_data.get('text')
        model_name = json_data.get('model', 'en')
        try:
            model = get_model(model_name)
            entities = Entities(model, text)
            resp.body = json.dumps(entities.to_json(), sort_keys=True,
                                   indent=2)
            resp.content_type = 'text/string'
            resp.append_header('Access-Control-Allow-Origin', "*")
            resp.status = falcon.HTTP_200
        except Exception:
            resp.status = falcon.HTTP_500

for model in MODELS:
  print("Load model ", model)
  get_model(model)

app = falcon.API()
app.add_route('/dep', DepResource())
app.add_route('/ent', EntResource())
app.add_route('/{model_name}/schema', SchemaResource())
app.add_route('/models', ModelsResource())
app.add_route('/version', VersionResource())
app.add_route('/', VersionResource())
