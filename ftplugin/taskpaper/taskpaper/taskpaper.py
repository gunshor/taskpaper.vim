#!/usr/bin/env python
# encoding: utf-8

import re
from collections import defaultdict
import sys

try: import vim
except ImportError: pass

from config import *

from _ordered_dict import OrderedDict

_TAGS = re.compile(r"\s*(@\w+)(\([^)]*\))?\s*")
def _extract_tags(text):
    tags = OrderedDict()

    def _found(m):
        name = m.group(1).strip()
        value = m.group(2)
        if value: value = value[1:-1].strip()
        tags[name] = Tag(name, value)
        return ""
    new_text = _TAGS.subn(_found, text)[0]

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

    def deep_iterate(self):
        """Iterate over all children, including their children"""
        yield self
        for c in self.childs:
            for sc in c.deep_iterate():
                yield sc
    __iter__ = deep_iterate

    def flat_iterate(self):
        """Only iterate over self and the children"""
        yield self
        for c in self.childs:
            yield c

    @property
    def prev(self):
        if self.parent:
            idx = self.parent.childs.index(self)
            if idx == 0: return self.parent
            return self.parent.childs[idx-1]

    def delete(self):
        if self.prev:
            self.prev._trailing_empty_lines += self._trailing_empty_lines
        if self.parent:
            self.parent.childs.remove(self)

        self._trailing_empty_lines = 0
        self.parent = None

    @property
    def text_with_tags(self):
        s = self.text or ""
        if len(self.tags):
            s += " " + ' '.join(str(t) for t in self.tags.values())
        s += '\n'
        return s

    def __getitem__(self, text):
        for c in self:
            if c.text == text: return c
        raise KeyError("No child with text %r!" % text)

    def __str__(self):
        s = "" if not self.indent else "\t" * self.indent

        if self.text:
            s += self.text_with_tags

        for c in self.childs:
            s += str(c)

        s += '\n' * self._trailing_empty_lines
        return s

    def __lt__(self, o):
        return self.lineno < o.lineno
    def __le__(self, o):
        return self.lineno <= o.lineno

class TaskPaperFile(TextItem):
    __INDENT = re.compile(r"^(\t*)(.*)")
    __ORDER = re.compile(r"o:(\S+)")

    def __init__(self, text):
        TextItem.__init__(self, None, None, None, None)

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
            elif _extract_tags(content)[0].strip()[-1] == ':':
                content = content.strip()
                line_type = Project

            to = line_type(indent, content, le, lidx + 1)

            if not to.parent:
                self.childs.append(to)
                to.parent = self

            le = to

    def filter(self, cmdline):
        m = self.__ORDER.search(cmdline)
        key = None
        reverse = False

        if m is not None:
            cmdline = cmdline[:m.span(0)[0]] + cmdline[m.span(0)[1]:]
            ocmd = m.group(1)
            if ocmd[0] in '+-':
                if ocmd[0] == '-':
                    reverse = True
                ocmd = ocmd[1:]
            if ocmd[0] != '@':
                ocmd = '@' + ocmd
            key = lambda a: a.tags[ocmd].value if (ocmd in a.tags) else None

        def _eval(o):
            def _sub(m):
                t = m.group(1)
                if t in o.tags:
                    if o.tags[t].value is not None:
                        return " %r " % o.tags[t].value
                    return " True "
                return " False "

            eval_str = _TAGS.sub(_sub, cmdline).strip()
            return eval(eval_str) if eval_str else False

        matches = set()
        def _recurse(obj):
            if _eval(obj):
                matches.add(obj)
            else:
                for c in obj.childs:
                    _recurse(c)

        _recurse(self)

        return sorted(matches, key=key, reverse=reverse)


    def at_line(self, lineno):
        if lineno <= 0:
            raise IndexError("Line numbers start at 1!")

        for c in self:
            if c.lineno == lineno: return c

class Project(TextItem):
    def __init__(self, *args):
        TextItem.__init__(self, *args)

        self._extract_tags()

    @property
    def text_without_markers(self):
        return self.text.rstrip()[:-1]


class Task(TextItem):
    def __init__(self, *args):
        TextItem.__init__(self, *args)

        self._extract_tags()

    @property
    def text_without_markers(self):
        return self.text.lstrip()[2:]

class CommentLine(TextItem):
    def __init__(self, *args):
        TextItem.__init__(self, *args)

    @property
    def text_without_markers(self):
        return self.text

class Tag(object):
    def __init__(self, name, value = None):
        self.name = name
        self.value = value
        if value is not None:
            for t in (int, float):
                try:
                    self.value = t(value)
                    break
                except ValueError:
                    pass

    def __str__(self):
        return self.name if not self.value else "%s(%s)" % \
                (self.name, self.value)

import datetime as dt
from copy import copy

str2date = lambda sdate: dt.date(*map(int,sdate.split('-')))
date2str = lambda date: date.strftime("%Y-%m-%d")

def extract_timeline(tpf, gtoday = None):
    tl = TaskPaperFile("")
    today = dt.date.today() if not gtoday else gtoday
    today_str = date2str(today)

    projects = {}
    for o in tpf:
        try:
            if "@due" in o.tags and not '@done' in o.tags:
                dd = o.tags["@due"].value.split()[0]
                other_date = str2date(dd)
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
                ad.indent = 1
                projects[dd].childs.append(ad)
                ad.parent = projects[dd]
        except Exception, e:
                raise RuntimeError("%s\n\nError in todo file in line %i: %s!" %
                        (str(e), o.lineno, o.text))

    outstr = '\n'.join(str(c) for c in sorted(tl.childs, key=lambda p: p.due))
    outstr += '\n\n vim:ro\n'

    return outstr

def log_finished(tpf, gtoday = None):
    logbook = TaskPaperFile("") if not os.path.exists(LOGBOOK_FILENAME) \
            else TaskPaperFile(open(LOGBOOK_FILENAME).read())

    new_tpf = TaskPaperFile(str(tpf))
    new_logbook = TaskPaperFile(str(logbook))

    today = dt.date.today() if not gtoday else gtoday

    # Important, we remove elements from the TPF, so we have to make a lists of
    # them first, otherwise the tree changes while traversing
    done_items = defaultdict(list)
    for e in list(new_tpf):
        if isinstance(e, (Task, Project)) and '@done' in e.tags:
            done_date = str2date(e.tags['@done'].value) if \
                    e.tags['@done'].value else today
            done_items[done_date].append(e)
            parents = []
            p = e.parent
            while isinstance(p, (Project, Task)):
                parents.append(p.text_without_markers)
                p = p.parent
            e.text = ' • '.join(parents[::-1] + [e.text_without_markers])
            if isinstance(e, Task):
                e.text = "- " + e.text
            else:
                e.text += ":"
            indent_diff = 1 - e.indent
            for c in e: c.indent += indent_diff
            e.delete()

    for date in sorted(done_items.keys(), reverse=True):
        proj_name = date.strftime("%A, %d. %B %Y:")
        proj = None
        try:
            proj = new_logbook[proj_name]
        except KeyError:
            proj = Project(0, proj_name, None, 1)
            new_logbook.childs.insert(0, proj)

        for task in done_items[date]:
            proj.childs.append(task)
            task.parent = proj

    new_logbook.childs.sort(
        key=lambda a: dt.datetime.strptime(a.text, "%A, %d. %B %Y:").date(),
        reverse=True,
    )
    for c in new_logbook: c._trailing_empty_lines = 0

    open(LOGBOOK_FILENAME, "w").write(
        str(TaskPaperFile('\n'.join(str(c) for c in new_logbook.childs)))
    )

    return new_tpf


def reorder_tags(tpf):
    for obj in tpf:
        tag_order = sorted([t.name for t in obj.tags.values() if not t.value]) + \
                    sorted([t.name for t in obj.tags.values() if t.value])
        for tn in tag_order:
            obj.tags[tn] = obj.tags.pop(tn)


def filter_jump(fn):
    line = int(vim.current.line.split('|', 2)[1])
    for idx,win in enumerate(vim.windows, 1):
        vim.command("%iwincmd w" % idx)
        if vim.eval("expand('%')").startswith(fn):
            break

    vim.current.window.cursor = line, 0
    vim.command('normal ^')


def filter_taskpaper(cmdline):
    all_windows = [ w for w in vim.windows ]
    cwind = all_windows.index(vim.current.window)

    def _close_all():
        for idx,win in enumerate(vim.windows, 1):
            vim.command("%iwincmd w" % idx)
            if "nofile" in vim.eval("&buftype"):
                vim.command(":bwipeout")
                return _close_all()
    _close_all()
    vim.command("%iwincmd w" % cwind)

    f = TaskPaperFile('\n'.join(vim.current.buffer))
    cf = vim.eval("expand('%')")

    matches = f.filter(cmdline)

    # new vim buffer
    cfb = os.path.splitext(cf)[0]
    vim.command("rightbelow new")
    vim.current.buffer[:] = [ "%s|%4i|%s" % (cfb, o.lineno, o.text_with_tags.strip()) for o in matches ]

    vim.command("resize 15")
    vim.command("setlocal winfixheight")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal ft=qf")
    vim.command("setlocal nomodifiable")
    vim.command("map <buffer> <cr> :py filter_jump('%s')<cr>" % cf)

def run_presave():
    tpf = TaskPaperFile('\n'.join(vim.current.buffer))

    reorder_tags(tpf)

    if os.path.basename(vim.current.buffer.name) == os.path.basename(TODO_FILENAME):
        open(TIMELINE_FILENAME, "w").write(extract_timeline(tpf))

    vim.current.buffer[:] = str(tpf).splitlines()


if __name__ == '__main__':
    from optparse import OptionParser

    def parse_args():
        parser = OptionParser("%prog [options] <input file>")
        parser.add_option("-t", "--timeline", action="store_true",
                default=False, help="create a timeline", metavar="FILE")
        parser.add_option("-l", "--logbook", action="store_true",
                default=False, help="update the logbook with done items", metavar="FILE")

        o, a = parser.parse_args()

        if not len(a):
            parser.error("Need at least the input file!")

        return o,a

    def main():
        o, a = parse_args()

        tpf = TaskPaperFile(open(a[0]).read())

        if o.logbook:
            tpf = log_finished(tpf)

        if o.timeline:
            open(TIMELINE_FILENAME, "w").write(extract_timeline(tpf))

        open(a[0], "w").write(str(tpf))

    main()

