#!/usr/bin/env python
# encoding: utf-8

import os
import os.path as p

HOME = os.getenv("HOME")

INBOX_FILENAME = p.join(HOME, "SimpleText", "01_inbox.taskpaper")
TODO_FILENAME = p.join(HOME, "SimpleText", "02_todo.taskpaper")
TIMELINE_FILENAME = p.join(HOME, "SimpleText", "10_timeline.taskpaper")
