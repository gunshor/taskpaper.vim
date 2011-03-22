#!/usr/bin/env python
# encoding: utf-8

try:
    import vim
except ImportError:
    pass

import re
import sys

from _ordered_dict import OrderedDict

__TAGS = re.compile(r"\s*(@\w+)(\([^)]*\))?\s*")
def _extract_tags(text):
    tags = OrderedDict()

    def _found(m):
        name = m.group(1).strip()
        value = m.group(2)
        if value: value = value[1:-1].strip()
        tags[name] = Tag(name, value)
        return ""
    new_text = __TAGS.subn(_found, text)[0]

    return new_text, tags


class TextItem(object):
    def __init__(self, indent, text, prev, lineno):
        self.childs = []
        self.lineno = lineno

        # Search the parent
        pparent = prev
        while pparent.indent >= indent:
            pparent = pparent.parent
        self.parent = pparent

        self.parent.childs.append(self)

        self.indent = indent
        self.text = text

        self.tags = {}

        self._trailing_empty_lines = 0

    def append_trailing_empty_line(self):
        self._trailing_empty_lines += 1

    def _extract_tags(self):
        self.text, self.tags = _extract_tags(self.text)

    @property
    def text_with_tags(self):
        s = self.text or ""
        if len(self.tags):
            s += " " + ' '.join(str(t) for t in self.tags.values())
        s += '\n'
        return s

    def __str__(self):
        s = "" if not self.indent else "\t" * self.indent

        if self.text:
            s += self.text_with_tags

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
        self.tags = {}

        self._trailing_empty_lines = 0

        le = self
        for lidx,line in enumerate(text.splitlines()):
            if not len(line.strip()):
                if le: le.append_trailing_empty_line()
                continue

            m = self.__INDENT.match(line)
            indent = len(m.group(1))
            content = m.group(2)

            line_type = CommentLine
            if content[0] == '-':
                line_type = Task
            elif _extract_tags(content)[0][-1] == ':':
                line_type = Project

            to = line_type(indent, content, le, lidx + 1)

            if not to.parent:
                self.childs.append(to)
            le = to


class Project(TextItem):
    def __init__(self, *args):
        TextItem.__init__(self, *args)

        self._extract_tags()

class Task(TextItem):
    def __init__(self, *args):
        TextItem.__init__(self, *args)

        self._extract_tags()

class CommentLine(TextItem):
    def __init__(self, *args):
        TextItem.__init__(self, *args)

class Tag(object):
    def __init__(self, name, value = None):
        self.name = name
        self.value = value

    def __str__(self):
        return self.name if not self.value else "%s(%s)" % \
                (self.name, self.value)

import os
import datetime as dt
from copy import deepcopy as copy

def extract_timeline():
    f = TaskPaperFile('\n'.join(vim.current.buffer))
    tl = TaskPaperFile("")
    today = dt.date.today().strftime("%Y-%m-%d")

    projects = {}
    def _recurse(f):
        if "@due" in f.tags and not '@done' in f.tags:
            dd = f.tags["@due"].value.split()[0]
            text = dt.date(*map(int,dd.split('-'))).strftime("%A, %d. %B %Y:")
            if today > dd:
                text = "Overdue:"
                dd = ".00_overdue"
            if today == dd:
                text = "Today:"
                dd = ".01_today"

            if dd not in projects:
                p = Project(0, text, tl, 0)
                p.due = dd
                projects[dd] = p

            ad = copy(f)
            ad._trailing_empty_lines = 0
            projects[dd].childs.append(ad)
            ad.parent = projects[dd]

        for c in f.childs:
            _recurse(c)

    _recurse(f)

    home = os.getenv("HOME")
    open("%s/SimpleText/timeline.taskpaper" % home, "w").write(
      '\n'.join(str(c) for c in sorted(tl.childs, key=lambda p: p.due))
    )

def reorder_tags():
    f = TaskPaperFile('\n'.join(vim.current.buffer))

    def _recurse(obj):
        tag_order = sorted([t.name for t in obj.tags.values() if not t.value]) + \
                    sorted([t.name for t in obj.tags.values() if t.value])
        for tn in tag_order:
            obj.tags[tn] = obj.tags.pop(tn)

        for c in obj.childs:
            _recurse(c)

    _recurse(f)

    vim.current.buffer[:] = str(f).splitlines()

def filter_taskpaper(cmdline):
    f = TaskPaperFile('\n'.join(vim.current.buffer))

    def _eval(o):
        def _sub(m):
            t = m.group(1)
            if t in o.tags: return " True "
            return " False "

        eval_str = __TAGS.sub(_sub, cmdline).strip()
        return eval(eval_str) if eval_str else False

    matches = set()
    cf = vim.eval("expand('%')")
    def _recurse(obj):
        if _eval(obj):
            matches.add("%s:%i:%s" % (cf, obj.lineno, obj.text_with_tags.strip()))
        else:
            for c in obj.childs:
                _recurse(c)

    _recurse(f)

    vim.command('lgetexpr "%s"' %
            ('\\n'.join(f.replace('"', r'\"') for f in sorted(matches)))
    )
    vim.command("lwindow")



def run_presave():
    reorder_tags()
    extract_timeline()


