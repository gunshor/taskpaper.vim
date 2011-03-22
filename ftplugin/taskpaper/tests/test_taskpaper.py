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

class TestExtractTags(unittest.TestCase):
    def test_simple(self):
        text, tags = extract_tags("Hello World @done @due(today) @uuid(123-abc-ef)")
        tnames = sorted(tags.keys())
        tvalues = [tags[n]._value for n in tnames]
        self.assertEqual(["@done", "@due", "@uuid"], tnames)
        self.assertEqual([None, "today", "123-abc-ef"], tvalues)
        self.assertEqual("Hello World", text)

class _ParsingBase(unittest.TestCase):
    text = None

    def setUp(self):
        self.tpf = TaskPaperFile(self.text)

        self.assertEqual(self.text, str(self.tpf))

class TestParsingSimple(_ParsingBase):
    text = \
"""One project:
	This is a comment
	which is continued on
	- Task one
		And a comment for Task one
"""

    def test_tree(self):
        self.assertEqual(1, len(self.tpf.childs))
        p = self.tpf.childs[0]

        self.assertEqual("One project:", p.text)
        self.assertEqual("Project", p.__class__.__name__)
        self.assertEqual(3, len(p.childs))

        self.assertEqual("This is a comment", p.childs[0].text)
        self.assertEqual("CommentLine", p.childs[0].__class__.__name__)

        self.assertEqual("which is continued on", p.childs[1].text)
        self.assertEqual("CommentLine", p.childs[1].__class__.__name__)

        self.assertEqual("- Task one", p.childs[2].text)
        self.assertEqual("Task", p.childs[2].__class__.__name__)

        t = p.childs[2]
        self.assertEqual("- Task one", t.text)
        self.assertEqual("Task", t.__class__.__name__)
        self.assertEqual(1, len(t.childs))

        self.assertEqual("And a comment for Task one", t.childs[0].text)
        self.assertEqual("CommentLine", t.childs[0].__class__.__name__)





if __name__ == '__main__':
   unittest.main()
   # k = SomeTestClass()
   # unittest.TextTestRunner().run(k)

