#!/usr/bin/env python
# encoding: utf-8

import unittest

import os, sys
sys.path.append(os.path.dirname(__file__) + os.path.sep + '..')

from taskpaper import *


class TestTag(unittest.TestCase):
    def setUp(self):
        self.t1 = Tag("@done")
        self.t2 = Tag("@due", "2011-09-14")

    def test_str(self):
        self.assertEqual("@done", str(self.t1))
        self.assertEqual("@due(2011-09-14)", str(self.t2))

class _DummyTextItem(TextItem):
    def __init__(self, text):
        self.text = text
        self.tags = {}

        self._extract_tags()

class TestExtractTags(unittest.TestCase):
    def test_simple(self):
        d = _DummyTextItem("Hello World @done @due(today) @uuid(123-abc-ef)")
        tnames = sorted(d.tags.keys())
        tvalues = [d.tags[n].value for n in tnames]
        self.assertEqual(["@done", "@due", "@uuid"], tnames)
        self.assertEqual([None, "today", "123-abc-ef"], tvalues)
        self.assertEqual("Hello World", d.text)

    def test_with_paren(self):
        d = _DummyTextItem("(@done and not @work) or @home")
        self.assertEqual(["@done", "@work", "@home"], d.tags.keys())

    def test_with_numbers(self):
        d = _DummyTextItem("Blah @ka2wi @andAnother")
        self.assertEqual(["@ka2wi", "@andAnother"], d.tags.keys())

class _ParsingBase(unittest.TestCase):
    text = None

    def setUp(self):
        self.tpf = TaskPaperFile(self.text)

        self.assertEqual(self.text, str(self.tpf))

class TestParsingSimple(_ParsingBase):
    text = \
"""One project:
	This is a comment
	which is continued on @thisisnotag
	- Task one
		And a comment for Task one
	- Task two
"""

    def test_tree(self):
        self.assertEqual(1, len(self.tpf.childs))
        p = self.tpf.childs[0]

        self.assertEqual("One project:", p.text)
        self.assertEqual("Project", p.__class__.__name__)
        self.assertEqual(4, len(p.childs))

        self.assertEqual("This is a comment", p.childs[0].text)
        self.assertEqual("CommentLine", p.childs[0].__class__.__name__)

        self.assertEqual("which is continued on @thisisnotag", p.childs[1].text)
        self.assertEqual("CommentLine", p.childs[1].__class__.__name__)

        self.assertEqual("- Task one", p.childs[2].text)
        self.assertEqual("Task", p.childs[2].__class__.__name__)

        self.assertEqual("- Task two", p.childs[3].text)
        self.assertEqual("Task", p.childs[2].__class__.__name__)

        t = p.childs[2]
        self.assertEqual("- Task one", t.text)
        self.assertEqual("Task", t.__class__.__name__)
        self.assertEqual(1, len(t.childs))

        self.assertEqual("And a comment for Task one", t.childs[0].text)
        self.assertEqual("CommentLine", t.childs[0].__class__.__name__)


class TestParsingWithEmptyLines(TestParsingSimple):
    text = \
"""One project:
	This is a comment
	which is continued on @thisisnotag

	- Task one
		And a comment for Task one

	- Task two

"""

class TestParsingWithTags(TestParsingSimple):
    text = \
"""One project: @btag @atag @due(2011-09-13)
	This is a comment
	which is continued on @thisisnotag

	- Task one @today
		And a comment for Task one

	- Task two @worldDomination
"""

    def test_tags(self):
        p = self.tpf.childs[0]
        self.assertEqual(["@btag", "@atag", "@due"], p.tags.keys())
        self.assertEqual(["@btag", "@atag", "@due"], [ t.name for t in p.tags.values()])
        self.assertEqual([None, None, "2011-09-13"], [ t.value for t in p.tags.values()])

        self.assertEqual(0, len(p.childs[0].tags))
        self.assertEqual(0, len(p.childs[1].tags))

        self.assertEqual(1, len(p.childs[2].tags))
        self.assertEqual(1, len(p.childs[3].tags))

