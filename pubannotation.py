#!/usr/bin/env python

"""PubAnnotation format support.

See http://www.pubannotation.org/docs/format/ for the PubAnnotation
format specification.
"""

import sys
import json
import six
import re

from itertools import chain

# PubAnnotation URIs for OA JSON-LD conversion
pa_subj = 'pa:Subject'
pa_pred = 'pa:Predicate'
pa_obj  = 'pa:Object'

class Annotation(object):
    def __init__(self, id_):
        self.id = id_

    def resolve_ids(self, ann_by_id):
        """Replace IDs with the corresponding annotation objects."""
        raise NotImplementedError

    def spans(self):
        """Return list of (start, end) pairs identifying annotation spans."""
        raise NotImplementedError

    def target(self):
        """Return annotation target in OA JSON-LD format."""
        def wrap(span):
            return 'span:%d,%d' % (span[0], span[1])
        spans = self.spans()
        if len(spans) == 1:
            return wrap(spans[0])
        else:
            return [wrap(s) for s in spans]

    def __str__(self):
        return pretty(self.to_json())

    def to_json(self):
        """Return dict in the PubAnnotation JSON format."""
        raise NotImplementedError

    def to_jsonld(self):
        """Return dict in the Open Annotation recommended JSON-LD format."""
        raise NotImplementedError

    @classmethod
    def from_json(cls, s):
        """Return Annotation from dict in the PubAnnotation JSON format."""
        raise NotImplementedError

    @classmethod
    def from_jsonld(cls, s):
        """Return Annotation from dict in the Open Annotation
        recommended JSON-LD format."""
        raise NotImplementedError

class Denotation(Annotation):
    def __init__(self, id_, begin, end, obj):
        self.id = id_
        self.begin = begin
        self.end = end
        self.obj = obj

    def resolve_ids(self, ann_by_id):
        """Replace IDs with the corresponding annotation objects."""
        pass

    def spans(self):
        """Return list of (start, end) pairs identifying annotation spans."""
        return [(self.begin, self.end)]

    def to_json(self):
        """Return dict in the PubAnnotation JSON format."""
        doc = {
            'id': self.id,
            'span': {
                'begin': self.begin,
                'end': self.end,
            },
            'obj': self.obj,
        }
        return doc

    def to_jsonld(self):
        """Return dict in the Open Annotation recommended JSON-LD format."""
        doc = {
            '@id': self.id,
            '@type': 'pa:Denotation',
            'hasTarget': self.target(),
            'label': self.obj,
        }
        return doc

    @classmethod
    def from_json(cls, doc):
        """Return Denotation from dict in the PubAnnotation JSON format."""
        span = doc.get('span', {})
        return cls(
            id_=doc.get('id'),
            begin=span.get('begin'),
            end=span.get('end'),
            obj=doc.get('obj')
        )

    @classmethod
    def from_jsonld(cls, doc):
        """Return Denotation from dict in the Open Annotation
        recommended JSON-LD format."""
        target = doc['hasTarget']
        m = re.match(r'span:(\d+),(\d+)', target)
        begin, end = m.groups()
        return cls(
            id_=doc.get('@id'),
            begin=int(begin),
            end=int(end),
            obj=doc.get('label')
        )
    
class Relation(Annotation):
    def __init__(self, id_, subj, pred, obj):
        self.id = id_
        self.subj = subj
        self.pred = pred
        self.obj = obj

    def resolve_ids(self, ann_by_id):
        """Replace IDs with the corresponding annotation objects."""
        assert isinstance(self.subj, six.string_types), 'multiple resolve?'
        assert isinstance(self.obj, six.string_types), 'multiple resolve?'
        assert self.subj in ann_by_id, 'missing ID %s' % self.subj
        assert self.obj in ann_by_id, 'missing ID %s' % self.obj
        self.subj = ann_by_id[self.subj]
        self.obj = ann_by_id[self.obj]

    def spans(self):
        """Return list of (start, end) pairs identifying annotation spans."""
        assert isinstance(self.subj, Annotation), 'resolve_ids() first'
        assert isinstance(self.obj, Annotation), 'resolve_ids() first'
        return [(self.subj.begin, self.subj.end),
                (self.obj.begin, self.obj.end)]

    def subj_id(self):
        """Return the ID of the Relation subject."""
        if isinstance(self.subj, six.string_types):
            return self.subj
        else:
            return self.subj.id

    def obj_id(self):
        """Return the ID of the Relation object."""
        if isinstance(self.obj, six.string_types):
            return self.obj
        else:
            return self.obj.id

    def to_json(self):
        """Return dict in the PubAnnotation JSON format."""
        doc = {
            'id': self.id,
            'subj': self.subj_id(),
            'pred': self.pred,
            'obj': self.obj_id(),
        }
        return doc

    def to_jsonld(self):
        """Return dict in the Open Annotation recommended JSON-LD format."""
        doc = {
            '@id': self.id,
            '@type': 'pa:Relation',
            'hasTarget': self.target(),
            'hasBody': {
                pa_subj: self.subj_id(),
                pa_pred: self.pred,
                pa_obj:  self.obj_id(),
            }
        }
        return doc

    @classmethod
    def from_json(cls, doc):
        """Return Relation from dict in the PubAnnotation JSON format."""
        return cls(
            id_=doc.get('id'),
            subj=doc.get('subj'),
            pred=doc.get('pred'),
            obj=doc.get('obj')
        )

    @classmethod
    def from_jsonld(cls, doc):
        """Return Relation from dict in the Open Annotation
        recommended JSON-LD format."""
        body = doc.get('hasBody')
        return cls(
            id_=doc.get('@id'),
            subj=body.get(pa_subj),
            pred=body.get(pa_pred),
            obj=body.get(pa_obj)
        )

class Modification(Annotation):
    def __init__(self, id_, pred, obj):
        self.id = id_
        self.pred = pred
        self.obj = obj

    def resolve_ids(self, ann_by_id):
        """Replace IDs with the corresponding annotation objects."""
        assert isinstance(self.obj, six.string_types), 'multiple resolve?'
        assert self.obj in ann_by_id, 'missing ID %s' % self.obj
        self.obj = ann_by_id[self.obj]

    def spans(self):
        """Return list of (start, end) pairs identifying annotation spans."""
        assert isinstance(self.obj, Annotation), 'resolve_ids() first'
        return [(self.obj.begin, self.obj.end)]

    def obj_id(self):
        """Return the ID of the Relation object."""
        if isinstance(self.obj, six.string_types):
            return self.obj
        else:
            return self.obj.id

    def to_json(self):
        """Return dict in the PubAnnotation JSON format."""
        doc = {
            'id': self.id,
            'pred': self.pred,
            'obj': self.obj_id(),
        }
        return doc

    def to_jsonld(self):
        """Return dict in the Open Annotation recommended JSON-LD format."""
        doc = {
            '@id': self.id,
            '@type': 'pa:Modification',
            'hasTarget': self.target(),
            'hasBody': {
                pa_pred: self.pred,
                pa_obj: self.obj_id(),
            }
        }
        return doc

    @classmethod
    def from_json(cls, doc):
        """Return Modification from dict in the PubAnnotation JSON format."""
        return cls(id_=doc.get('id'),
                   pred=doc.get('pred'),
                   obj=doc.get('obj'))

    @classmethod
    def from_jsonld(cls, doc):
        """Return Modification from dict in the Open Annotation
        recommended JSON-LD format."""
        body = doc.get('hasBody')
        return cls(
            id_=doc.get('@id'),
            pred=body.get(pa_pred),
            obj=body.get(pa_obj)
        )

class Annotations(object):
    """Represents PubAnnotation annotations for a document."""
    def __init__(self, target, text, project, sourcedb, sourceid, divid,
                 denotations, relations, modifications, namespaces):
        self.target = target
        self.text = text
        self.project = project
        self.sourcedb = sourcedb
        self.sourceid = sourceid
        self.divid = divid
        self.denotations = denotations
        self.relations = relations
        self.modifications = modifications
        self.namespaces = namespaces
        self._ids_resolved = False

    def annotations(self):
        return chain(self.denotations, self.relations, self.modifications)

    def get_ann_by_id(self):
        ann_by_id = {}
        for a in self.annotations():
            assert a.id not in ann_by_id, 'duplicate id %s' % id
            ann_by_id[a.id] = a
        return ann_by_id

    def resolve_ids(self, ann_by_id=None):
        """Resolves ID references into object references."""
        if self._ids_resolved:
            return
        if ann_by_id is None:
            ann_by_id = self.get_ann_by_id()
        for a in self.annotations():
            a.resolve_ids(ann_by_id)
        self._ids_resolved = True

    def base_url(self):
        """Return OA JSON-LD @base URL for Annotations."""
        root = 'http://pubannotation.org/projects/'
        base = root + '%s/docs/sourcedb/%s/sourceid/%s/' % \
            (self.project, self.sourcedb, self.sourceid)
        if self.divid is not None:
            base += 'divs/%s/' % self.divid
        return base

    @staticmethod
    def parse_base(base):
        """Parse OA JSON-LD @base URL into properties of Annotations."""
        m = re.match(r'^http://pubannotation.org/projects/(.*?)/docs/sourcedb/(.*?)/sourceid/(.*?)/(?:divs/(.*?)/)?$', base)
        assert m, 'failed to parse %s' % base
        return m.groups()

    def __str__(self):
        return pretty(self.to_json())

    def to_json(self):
        """Return dict in the PubAnnotation JSON format."""
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
            if doc[k] is None or doc[k] == []:
                del doc[k]
        return doc

    def to_jsonld(self):
        """Return dict in the Open Annotation recommended JSON-LD format."""
        self.resolve_ids()
        doc = {
            '@context': {
                '@base': self.base_url(),
                'text': self.text, # TODO: eliminate
            },
            '@graph': [
                a.to_jsonld() for a in self.annotations()
            ]
        }
        return doc
        
    @classmethod
    def from_json(cls, doc):
        denotations = doc.get('denotations', [])
        relations = doc.get('relations', [])
        modifications = doc.get('modifications', [])
        denotations = [Denotation.from_json(d) for d in denotations]
        relations = [Relation.from_json(r) for r in relations]
        modifications = [Modification.from_json(m) for m in modifications]
        return cls(target=doc.get('target'),
                   text=doc.get('text'),
                   project=doc.get('project'),
                   sourcedb=doc.get('sourcedb'),
                   sourceid=doc.get('sourceid'),
                   divid=doc.get('divid'),
                   denotations=denotations,
                   relations=relations,
                   modifications=modifications,
                   namespaces=doc.get('namespaces', [])
                   )

    @classmethod
    def from_jsonld(cls, doc):
        context = doc['@context']
        graph = doc['@graph']
        base = context['@base']
        project, sourcedb, sourceid, divid = Annotations.parse_base(base)
        target_root = 'http://pubannotation.org/docs/sourcedb/'
        target = target_root + '%s/sourceid/%s/' % (sourcedb, sourceid)
        if divid is not None:
            target += 'divs/%s' % divid
            divid = int(divid)
        denotations =   [d for d in graph if d['@type'] == 'pa:Denotation']
        relations =     [r for r in graph if r['@type'] == 'pa:Relation']
        modifications = [m for m in graph if m['@type'] == 'pa:Modification']
        denotations = [Denotation.from_jsonld(d) for d in denotations]
        relations = [Relation.from_jsonld(r) for r in relations]
        modifications = [Modification.from_jsonld(m) for m in modifications]
        return cls(target=target,
                   text=context['text'],
                   project=project,
                   sourcedb=sourcedb,
                   sourceid=sourceid,
                   divid=divid,
                   denotations=denotations,
                   relations=relations,
                   modifications=modifications,
                   namespaces=[], # TODO
                   )

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
    # PubAnnotation JSON to python objects and back
    for i, doc in enumerate(docs):
        print 'test PA JSON', i
        anns = Annotations.from_json(doc)
        assert pretty(doc) == str(anns), 'failed roundtrip 1:\n%s\nvs.\n%s' % \
            (pretty(doc), str(anns))
    # PubAnnotation JSON to python objects to Open Annotation JSON-LD
    for i, doc in enumerate(docs):
        print 'test OA JSON', i
        anns = Annotations.from_json(doc)
        jsonldstr = pretty(anns.to_jsonld())
        anns2 = Annotations.from_jsonld(json.loads(jsonldstr))
        assert pretty(doc) == str(anns2), 'failed roundtrip 2:\n%s\nvs.\n%s' % \
            (pretty(doc), str(anns2))

def pretty(doc):
    return json.dumps(doc, sort_keys=True, indent=2, separators=(',', ': '))

def main(argv):
    docs = load_examples()
    test_roundtrips(docs)
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
