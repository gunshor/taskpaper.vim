#!/usr/bin/env python
# encoding: utf-8

try:
    import vim
except ImportError:
    pass

import re
import sys

from config import TIMELINE_FILENAME

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
        while pparent and pparent.indent >= indent:
            pparent = pparent.parent
        self.parent = pparent

        if self.parent:
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


class TaskPaperFile(object):
    __INDENT = re.compile("^(\t*)(.*)")

    def __init__(self, text):
        self.childs = []
        self.tags = {}

        le = None
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


    def __str__(self):
        return ''.join(str(c) for c in self.childs)



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

import datetime as dt
from copy import copy

def extract_timeline(tpf):
    tl = TaskPaperFile("")
    today = dt.date.today()
    today_str = today.strftime("%Y-%m-%d")

    projects = {}
    def _recurse(o):
        if "@due" in o.tags and not '@done' in o.tags:
            dd = o.tags["@due"].value.split()[0]
            other_date = dt.date(*map(int,dd.split('-')))
            diff_days = (other_date - today).days

            text = "%s (+%i day%s):" % (
                other_date.strftime("%A, %d. %B %Y"),
                diff_days, "s" if diff_days != 1 else ""
            )
            if today_str > dd:
                text = "Overdue:"
                dd = ".00_overdue"
            if today_str == dd:
                text = "Today:"
                dd = ".01_today"

            if dd not in projects:
                p = Project(0, text, None, 0)
                tl.childs.append(p)

                p.due = dd
                projects[dd] = p

            ad = copy(o)
            ad._trailing_empty_lines = 0
            projects[dd].childs.append(ad)
            ad.parent = projects[dd]

        for c in o.childs:
            _recurse(c)

    _recurse(tpf)

    open(TIMELINE_FILENAME, "w").write(
      '\n'.join(str(c) for c in sorted(tl.childs, key=lambda p: p.due))
    )

def reorder_tags(tpf):
    def _recurse(obj):
        tag_order = sorted([t.name for t in obj.tags.values() if not t.value]) + \
                    sorted([t.name for t in obj.tags.values() if t.value])
        for tn in tag_order:
            obj.tags[tn] = obj.tags.pop(tn)

        for c in obj.childs:
            _recurse(c)

    _recurse(tpf)

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
    tpf = TaskPaperFile('\n'.join(vim.current.buffer))

    reorder_tags(tpf)
    extract_timeline(tpf)

    vim.current.buffer[:] = str(tpf).splitlines()
