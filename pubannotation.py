#!/usr/bin/env python

"""PubAnnotation format support.

See http://www.pubannotation.org/docs/format/ for the PubAnnotation
format specification.
"""

import sys
import json

class Annotation(object):
    def __init__(self, id_):
        self.id = id_

    def to_json(self):
        pass

    @classmethod
    def from_json(cls, s):
        raise NotImplementedError

class Denotation(Annotation):
    def __init__(self, id_, begin, end, obj):
        self.id = id_
        self.begin = begin
        self.end = end
        self.obj = obj

    def to_json(self):
        doc = {
            'id': self.id,
            'span': {
                'begin': self.begin,
                'end': self.end,
            },
            'obj': self.obj,
        }
        return doc

    @classmethod
    def from_json(cls, doc):
        span = doc.get('span', {})
        return cls(id_=doc.get('id'),
                   begin=span.get('begin'),
                   end=span.get('end'),
                   obj=doc.get('obj'))
    
class Relation(Annotation):
    def __init__(self, id_, subj, pred, obj):
        self.id = id_
        self.subj = subj
        self.pred = pred
        self.obj = obj

    def to_json(self):
        doc = {
            'id': self.id,
            'subj': self.subj,
            'pred': self.pred,
            'obj': self.obj,
        }
        return doc

    @classmethod
    def from_json(cls, doc):
        return cls(id_=doc.get('id'),
                   subj=doc.get('subj'),
                   pred=doc.get('pred'),
                   obj=doc.get('obj'))

class Modification(Annotation):
    def __init__(self, id_, pred, obj):
        self.id = id_
        self.pred = pred
        self.obj = obj

    def to_json(self):
        doc = {
            'id': self.id,
            'pred': self.pred,
            'obj': self.obj,
        }
        return doc

    @classmethod
    def from_json(cls, doc):
        return cls(id_=doc.get('id'),
                   pred=doc.get('pred'),
                   obj=doc.get('obj'))

class Annotations(object):
    """Represents PubAnnotation annotations for a document."""
    def __init__(self, target, text, sourcedb, sourceid, divid, project,
                 denotations, relations, modifications, namespaces):
        self.target = target
        self.text = text
        self.sourcedb = sourcedb
        self.sourceid = sourceid
        self.divid = divid
        self.project = project
        self.denotations =   [Denotation.from_json(d) for d in denotations]
        self.relations =     [Relation.from_json(r) for r in relations]
        self.modifications = [Modification.from_json(m) for m in modifications]
        self.namespaces = namespaces

    def __str__(self):
        return pretty(self.to_json())

    def to_json(self):
        doc = {
            'target': self.target,
            'text': self.text,
            'sourcedb': self.sourcedb,
            'sourceid': self.sourceid,
            'divid': self.divid,
            'project': self.project,
            'namespaces': self.namespaces,
        }
        doc['denotations']   = [d.to_json() for d in self.denotations]
        doc['relations']     = [r.to_json() for r in self.relations]
        doc['modifications'] = [m.to_json() for m in self.modifications]
        for k in doc.keys():
            if doc[k] == []:
                del doc[k]
        return doc
        
    @classmethod
    def from_json(cls, doc):
        return cls(target=doc.get('target'),
                   text=doc.get('text'),
                   sourcedb=doc.get('sourcedb'),
                   sourceid=doc.get('sourceid'),
                   divid=doc.get('divid'),
                   project=doc.get('project'),
                   denotations=doc.get('denotations', []),
                   relations=doc.get('relations', []),
                   modifications=doc.get('modifications', []),
                   namespaces=doc.get('namespaces', []))

def load_examples():
    example_files = [
        'examples/mini.json',
        'examples/BioNLP-ST-2013-GE-PMC1310901-TIAB.json',
    ]
    examples = []
    for fn in example_files:
        with open(fn) as f:
            s = f.read()
            d = json.loads(s)
            examples.append(d)
    return examples

def test_roundtrips(docs):
    for doc in docs:
        anns = Annotations.from_json(doc)
        assert pretty(doc) == str(anns), 'failed roundtrip:\n%s\nvs.\n%s' % \
            (pretty(doc), str(anns))

def pretty(doc):
    return json.dumps(doc, sort_keys=True, indent=2, separators=(',', ': '))

def main(argv):
    # namespace example from http://pubannotation.org/projects/EVEX-test.json
    namespaces = [
        { "prefix": "GO", "uri": "http://identifiers.org/go/" }
        ]
    docs = load_examples()
    test_roundtrips(docs)
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
