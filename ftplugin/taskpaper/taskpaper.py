#!/usr/bin/env python
# encoding: utf-8

try:
    import vim
except ImportError:
    pass

import re
import uuid

class Tag(object):
    def __init__(self, name, value = None):
        self._name = name
        self._value = value

    def __str__(self):
        return self._name if not self._value else "%s(%s)" % \
                (self._name, self._value)

__TAGS = re.compile(r"\s*(@[^(\s]+)(\([^)]*\))?\s*")
def extract_tags(text):
    tags = {}
    def _found(m):
        name = m.group(1).strip()
        value = m.group(2)
        if value: value = value[1:-1].strip()
        tags[name] = Tag(name, value)
        return ""
    new_text = __TAGS.subn(_found, text)[0]
    return new_text, tags

def reorder_tags():
    result = []
    for l in vim.current.buffer:
        text, tags = extract_tags(l)

        id = tags.pop("@uuid", Tag("@uuid", str(uuid.uuid4())))
        tag_order = sorted([t._name for t in tags.values() if not t._value]) + \
                    sorted([t._name for t in tags.values() if t._value]) + \
                    ['@uuid']
        tags["@uuid"] = id

        result.append(' '.join((text,
            ' '.join(str(tags[n]) for n in tag_order)
        )))
    vim.current.buffer[:] = result



