#!/usr/bin/env python

import sys
import json

doc = json.loads(sys.stdin.read())
print json.dumps(doc, sort_keys=True, indent=4, separators=(',', ': '))
