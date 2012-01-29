#!/usr/bin/env python
# encoding: utf-8

import os
import os.path as p

HOME = os.getenv("HOME")

INBOX_FILENAME = p.join(HOME, "Dropbox", "Tasks", "01_inbox.taskpaper")
TODO_FILENAME = p.join(HOME, "Dropbox", "Tasks", "02_todo.taskpaper")
TIMELINE_FILENAME = p.join(HOME, "Dropbox", "Tasks", "10_timeline.taskpaper")
LOGBOOK_FILENAME = p.join(HOME, "Dropbox", "Tasks", "40_logbook.taskpaper")
