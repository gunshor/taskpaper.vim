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

if __name__ == '__main__':
   unittest.main()
   # k = SomeTestClass()
   # unittest.TextTestRunner().run(k)

