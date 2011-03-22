#!/usr/bin/env python
# encoding: utf-8

try:
    import vim
except ImportError:
    pass

import re

class TextItem(object):
    def __init__(self, indent, text, prev):
        self.childs = []

        # Search the parent
        self.parent = prev if prev.indent < indent else prev.parent
        self.parent.childs.append(self)

        self.indent = indent
        self.text = text

        self._trailing_empty_lines = 0

    def append_trailing_empty_line(self):
        self._trailing_empty_lines += 1


    def __str__(self):
        s = "" if not self.indent else "\t" * self.indent
        s += self.text + '\n' if self.text else ""
        for c in self.childs:
            s += str(c)

        s += '\n' * self._trailing_empty_lines
        return s


class TaskPaperFile(TextItem):
    __INDENT = re.compile("^(\t*)(.*)")

    def __init__(self, text):
        self.text = None
        self.childs = []
        self.indent = None
        self._trailing_empty_lines = 0

        le = self
        for line in text.splitlines():
            if not len(line.strip()):
                if le: le.append_trailing_empty_line()
                continue

            m = self.__INDENT.match(line)
            indent = len(m.group(1))
            content = m.group(2)

            line_type = CommentLine
            if content[0] == '-':
                line_type = Task
            elif extract_tags(content)[0][-1] == ':':
                line_type = Project

            to = line_type(indent, content, le)

            if not to.parent:
                self.childs.append(to)
            le = to



class Project(TextItem):
    def __init__(self, indent, text, prev):
        TextItem.__init__(self, indent, text, prev)

        self.parent = prev if prev and prev.indent < indent else None
class Task(TextItem):
    def __init__(self, indent, text, prev):
        TextItem.__init__(self, indent, text, prev)


class CommentLine(TextItem):
    def __init__(self, indent, text, prev):
        TextItem.__init__(self, indent, text, prev)





    def append_trailing_empty_line(self):
        self._text += 1




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
    return
    result = []
    for l in vim.current.buffer:
        text, tags = extract_tags(l)

        tag_order = sorted([t._name for t in tags.values() if not t._value]) + \
                    sorted([t._name for t in tags.values() if t._value])
        result.append(' '.join((text,
            ' '.join(str(tags[n]) for n in tag_order)
        )))
    vim.current.buffer[:] = result



