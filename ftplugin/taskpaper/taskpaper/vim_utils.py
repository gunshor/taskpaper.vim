#!/usr/bin/env python
# encoding: utf-8

"""
Various helper functionality that is useful in Vim. You find stuff
here which I cannot implement in VimL directly because I do not
know the language very well or which acts as a bridge between Vim
and the TaskPaper Format
"""

import re
import datetime as dt

try: import vim
except ImportError: pass

from taskpaper import *

_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_NUM = re.compile(r"\d+")
def add_to_date(days, multiplier):
    if days == 0: days = 1
    else: days = days - int(vim.eval("line('.')")) + 1

    days *= multiplier

    cursor = vim.current.window.cursor
    col = cursor[-1]
    line = vim.current.line
    new_line = line
    new_col = cursor[-1]

    while col and line[col] not in " \t\n\r":
        col -= 1

    m = _DATE.search(line[col:])
    if m:
        d = str2date(m.group(0)) + dt.timedelta(days=days)
        new_line = line[:col+m.start()] + date2str(d)
        new_col = len(new_line) - 1
        new_line += line[col+m.end():]
    else:
        m = _NUM.search(line[col:])
        if m:
            d = int(m.group(0)) + days
            new_line = line[:col+m.start()] + str(d)
            new_col = len(new_line) - 1
            new_line += line[col+m.end():]

    vim.current.line = new_line
    vim.current.window.cursor = cursor[0], new_col

def toggle_done(last_line):
    line = vim.current.window.cursor[0]
    last_line = line + 1 if last_line == -1 else last_line + 1

    def _toggle_done(c):
        was_done = c.tags.pop('@done', None)
        if not was_done:
            c.tags['@done'] = Tag('@done', date2str(dt.date.today()))

    tpf = TaskPaperFile('\n'.join(vim.current.buffer))
    for i in range(line, last_line):
        c = tpf.at_line(i)
        if isinstance(c, (Task, Project)):
            _toggle_done(c)

    vim.current.buffer[:] = str(tpf).splitlines()
