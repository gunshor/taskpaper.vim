#!/usr/bin/env python
# encoding: utf-8

"""
Various helper functionality that is useful in Vim. You find stuff
here which I cannot implement in VimL directly because I do not
know the language very well or which acts as a bridge between Vim
and the TaskPaper Format
"""

import re
from datetime import timedelta

try: import vim
except ImportError: pass

from taskpaper import str2date, date2str

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
        d = str2date(m.group(0)) + timedelta(days=days)
        new_line = line[:col+m.start()] + date2str(d)
        new_col = len(new_line) - 1
        new_line += line[col+m.end():]
    else:
        m = _NUM.search(line[col:])
        print "m: %s" % (m)
        if m:
            d = int(m.group(0)) + days
            new_line = line[:col+m.start()] + str(d)
            new_col = len(new_line) - 1
            new_line += line[col+m.end():]

    vim.current.line = new_line
    vim.current.window.cursor = cursor[0], new_col

