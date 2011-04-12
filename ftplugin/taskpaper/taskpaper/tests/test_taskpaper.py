#!/usr/bin/env python
# encoding: utf-8

import unittest

import os, sys
sys.path.append(os.path.dirname(__file__) + os.path.sep + '..')

from taskpaper import *

########
# Tags #
########
# Tag class  {{{
class TestTag(unittest.TestCase):
    def setUp(self):
        self.t1 = Tag("@done")
        self.t2 = Tag("@due", "2011-09-14")

    def test_str(self):
        self.assertEqual("@done", str(self.t1))
        self.assertEqual("@due(2011-09-14)", str(self.t2))
# End: Tag class  }}}
# Parsing of Tags  {{{
class _DummyTextItem(TextItem):
    def __init__(self, text):
        self.text = text
        self.tags = {}

        self._extract_tags()

class TestParsingOfTags(unittest.TestCase):
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


# End: Parsing of Tags  }}}

#####################################
# Tests on Complete File (Read Only) #
#####################################
# TaskPaper File Tests Base Classes  {{{
class _TPFBaseTest(unittest.TestCase):
    text = None

    def setUp(self):
        self.tpf = TaskPaperFile(self.text)
class _ReadOnlyTPFBaseTest(_TPFBaseTest):
    def test_text_does_not_change(self):
        self.assertEqual(self.text, str(self.tpf))
# End: TaskPaper File Tests Base Classes  }}}
# Parsing Tests  {{{

class TestParsingSimple(_ReadOnlyTPFBaseTest):
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
        self.assertEqual(["@btag", "@atag", "@due"],
            [t.name for t in p.tags.values()]
        )
        self.assertEqual([None, None, "2011-09-13"],
            [t.value for t in p.tags.values()]
        )

        self.assertEqual(0, len(p.childs[0].tags))
        self.assertEqual(0, len(p.childs[1].tags))

        self.assertEqual(1, len(p.childs[2].tags))
        self.assertEqual(1, len(p.childs[3].tags))
# End: Parsing Tests  }}}
# Access Elements by Line Numbers  {{{
class TestAccessByLineNumbers(_ReadOnlyTPFBaseTest):
    text = \
"""One Project:
	A comment
	Another
	- A Task

	- Another
	A subproject:
			This is some written text
		- And one more task
"""

    def test_project(self):
        self.assertEqual("One Project:", self.tpf.at_line(1).text)

    def test_subproject(self):
        self.assertEqual("A subproject:", self.tpf.at_line(7).text)

    def test_task(self):
        self.assertEqual("- And one more task", self.tpf.at_line(9).text)

    def test_comment_1(self):
        self.assertEqual("A comment", self.tpf.at_line(2).text)
    def test_comment_2(self):
        self.assertEqual("Another", self.tpf.at_line(3).text)
    def test_comment_3(self):
        self.assertEqual("This is some written text", self.tpf.at_line(8).text)



# End: Access Element by Line Numbers }}}
# Timeline Tests  {{{
class _CreateTimelineBase(unittest.TestCase):
    def setUp(self):
        self.tpf = TaskPaperFile(self.text)
        self.timeline = extract_timeline(self.tpf, dt.date(2011, 04, 01))

    def runTest(self):
        self.assertEqual(self.wanted, str(self.timeline))

class TestTimeline_NoDueItemsInTodoFile(_CreateTimelineBase):
    text = "- This one has no due date @home"
    wanted = "\n\n vim:ro\n"

class TestTimeline_SimpleExample(_CreateTimelineBase):
    text = """My cool Project:
	- This was due @due(2011-03-20)
	- This is due tomorrow @due(2011-04-02)

My other cool Project:
	- This is due today @due(2011-04-01)
	- This is due in one month @due(2011-05-01)

My third cool project:
	- Nothing here
"""
    wanted = """Overdue:
	- This was due @due(2011-03-20)

Today:
	- This is due today @due(2011-04-01)

Saturday, 02. April 2011 (+1 day):
	- This is due tomorrow @due(2011-04-02)

Sunday, 01. May 2011 (+30 days):
	- This is due in one month @due(2011-05-01)


 vim:ro\n"""

class TestTimeline_SimpleExampleWithDones(_CreateTimelineBase):
    text = """My cool Project:
	- This was due @due(2011-03-20)
	- This is due tomorrow @due(2011-04-02) @done

My other cool Project:
	- This is due today @due(2011-04-01) @done
	- This is due in one month @due(2011-05-01)


My third cool project:
	- Nothing here
"""
    wanted = """Overdue:
	- This was due @due(2011-03-20)

Sunday, 01. May 2011 (+30 days):
	- This is due in one month @due(2011-05-01)


 vim:ro\n"""

class TestTimeline_OnlyIndentOnce(_CreateTimelineBase):
    text = """My cool Project:
	- This was due @due(2011-03-20)
	My subproject:
		- This is due today @due(2011-04-01)
"""
    wanted = """Overdue:
	- This was due @due(2011-03-20)

Today:
	- This is due today @due(2011-04-01)


 vim:ro\n"""

# End: Timeline Tests  }}}

#######################################
# Tests on Complete File (Read Write) #
#######################################
# Reordering of Tags  {{{
class _ReorderingOfTagsBase(_TPFBaseTest):
    def runTest(self):
        reorder_tags(self.tpf)
        self.assertEqual(self.wanted, str(self.tpf))

class TestTagReordering_simpleAlphabetical(_ReorderingOfTagsBase):
    text = "- was the dishes @beta @House @z\n"
    wanted = "- was the dishes @House @beta @z\n"
class TestTagReordering_withDataAtEnd(_ReorderingOfTagsBase):
    text = "- was the dishes @precision(1) @beta @House @z\n"
    wanted = "- was the dishes @House @beta @z @precision(1)\n"
class TestTagReordering_realWorldExample(_ReorderingOfTagsBase):
    text = """Keep things in order: @home @alp
	- One @due(today) @zshop @beta
	- Two @beta @alpha @due(tomorrow)
"""
    wanted = """Keep things in order: @alp @home
	- One @beta @zshop @due(today)
	- Two @alpha @beta @due(tomorrow)
"""
# End: Reordering of Tags  }}}


