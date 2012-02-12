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
from config import LOGBOOK_FILENAME

def _tpf_to_current_buffer(tpf):
    cursor = vim.current.window.cursor

    new_text = str(tpf).strip()
    old_text = '\n'.join(vim.current.buffer[:])
    if old_text != new_text:
        vim.current.buffer[:] = new_text.splitlines()
        vim.current.window.cursor = min(cursor[0], len(vim.current.buffer)), cursor[1]

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

    _tpf_to_current_buffer(tpf)

def log_current_dones():
    tpf, new_logbook = log_finished(TaskPaperFile('\n'.join(vim.current.buffer)))

    _tpf_to_current_buffer(tpf)

    open(LOGBOOK_FILENAME, "w").write(
        str(TaskPaperFile('\n'.join(str(c) for c in new_logbook.childs)))
    )

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

    _tpf_to_current_buffer(tpf)



