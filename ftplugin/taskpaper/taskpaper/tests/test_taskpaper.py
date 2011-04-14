#!/usr/bin/env python
# encoding: utf-8

import unittest

import os, sys
sys.path.append(os.path.dirname(__file__) + os.path.sep + '..')

from taskpaper import *

from nose.tools import raises, ok_, eq_

########
# Tags #
########
# Tag class  {{{
class TestTag(unittest.TestCase):
    def setUp(self):
        self.t1 = Tag("@done")
        self.t2 = Tag("@due", "2011-09-14")

    def test_str(self):
        eq_("@done", str(self.t1))
        eq_("@due(2011-09-14)", str(self.t2))
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
        eq_(["@done", "@due", "@uuid"], tnames)
        eq_([None, "today", "123-abc-ef"], tvalues)
        eq_("Hello World", d.text)

    def test_with_paren(self):
        d = _DummyTextItem("(@done and not @work) or @home")
        eq_(["@done", "@work", "@home"], d.tags.keys())

    def test_with_numbers(self):
        d = _DummyTextItem("Blah @ka2wi @andAnother")
        eq_(["@ka2wi", "@andAnother"], d.tags.keys())


# End: Parsing of Tags  }}}

#####################################
# Tests on Complete File (Read Only) #
#####################################
# TaskPaper File Tests Base Classes  {{{
class _TPFBaseTest(unittest.TestCase):
    text = None

    def setUp(self):
        self.tpf = TaskPaperFile(self.text)
class _KeepContentIntactTPFBaseTest(_TPFBaseTest):
    wanted = None

    def test_text_does_not_change(self):
        wanted = self.wanted or self.text
        eq_(wanted, str(self.tpf))
# End: TaskPaper File Tests Base Classes  }}}

# Parsing Tests  {{{
class TestParsingSimple(_KeepContentIntactTPFBaseTest):
    text = \
"""One project:
	This is a comment
	which is continued on @thisisnotag
	- Task one
		And a comment for Task one
	- Task two
"""

    def test_tree(self):
        eq_(1, len(self.tpf.childs))
        p = self.tpf.childs[0]

        eq_("One project:", p.text)
        eq_("Project", p.__class__.__name__)
        eq_(4, len(p.childs))

        eq_("This is a comment", p.childs[0].text)
        eq_("CommentLine", p.childs[0].__class__.__name__)

        eq_("which is continued on @thisisnotag", p.childs[1].text)
        eq_("CommentLine", p.childs[1].__class__.__name__)

        eq_("- Task one", p.childs[2].text)
        eq_("Task", p.childs[2].__class__.__name__)

        eq_("- Task two", p.childs[3].text)
        eq_("Task", p.childs[2].__class__.__name__)

        t = p.childs[2]
        eq_("- Task one", t.text)
        eq_("Task", t.__class__.__name__)
        eq_(1, len(t.childs))

        eq_("And a comment for Task one", t.childs[0].text)
        eq_("CommentLine", t.childs[0].__class__.__name__)

class TestParsingWithEmptyLines(TestParsingSimple):
    text = \
"""One project:
	This is a comment
	which is continued on @thisisnotag

	- Task one
		And a comment for Task one

	- Task two

"""


class TestParsingWithTrainlingSpaceInProject(TestParsingSimple):
    text = \
"One project: \n" + \
"""	This is a comment
	which is continued on @thisisnotag
	- Task one
		And a comment for Task one
	- Task two
"""
    wanted = "One project:\n" + \
"""	This is a comment
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
        eq_(["@btag", "@atag", "@due"], p.tags.keys())
        eq_(["@btag", "@atag", "@due"],
            [t.name for t in p.tags.values()]
        )
        eq_([None, None, "2011-09-13"],
            [t.value for t in p.tags.values()]
        )

        eq_(0, len(p.childs[0].tags))
        eq_(0, len(p.childs[1].tags))

        eq_(1, len(p.childs[2].tags))
        eq_(1, len(p.childs[3].tags))
# End: Parsing Tests  }}}
# Access Elements by Line Numbers  {{{
class TestAccessByLineNumbers(_KeepContentIntactTPFBaseTest):
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
        eq_("One Project:", self.tpf.at_line(1).text)

    def test_subproject(self):
        eq_("A subproject:", self.tpf.at_line(7).text)

    def test_task(self):
        eq_("- And one more task", self.tpf.at_line(9).text)

    def test_comment_1(self):
        eq_("A comment", self.tpf.at_line(2).text)
    def test_comment_2(self):
        eq_("Another", self.tpf.at_line(3).text)
    def test_comment_3(self):
        eq_("This is some written text", self.tpf.at_line(8).text)

    @raises(IndexError)
    def test_access_out_of_bounds_negativ(self):
        self.tpf.at_line(-1)

    @raises(IndexError)
    def test_access_out_of_bounds_zero(self):
        self.tpf.at_line(0)

    def test_access_out_of_bounds_too_high_returns_None(self):
        eq_(None, self.tpf.at_line(10))

# End: Access Element by Line Numbers }}}
# Access Elements by Text {{{
class TestAccessByText(_KeepContentIntactTPFBaseTest):
    text = \
"""One Project: @atag
	A comment @notag
	Another
	- A Task @anothertag @atag

	- Another @andanother
	A subproject: @btag
			This is some written text
		- And one more task @done
Another Project: @ctags
	- Year!
"""

    def test_project(self):
        p = self.tpf['Another Project:']
        ok_('@ctags' in p.tags)
        eq_(1, len(p.childs))
        eq_(10, p.lineno)

    def test_subproject(self):
        sp = self.tpf['A subproject:']
        ok_('@btag' in sp.tags)
        eq_(2, len(sp.childs))
        eq_(7, sp.lineno)

    def test_task(self):
        t = self.tpf['- And one more task']
        ok_('@done' in t.tags)
        eq_(0, len(t.childs))
        eq_(9, t.lineno)

    def test_comment_1(self):
        c = self.tpf['A comment @notag']
        eq_(0, len(c.childs))
        eq_(2, c.lineno)
    def test_comment_2(self):
        c = self.tpf['Another']
        eq_(0, len(c.childs))
        eq_(3, c.lineno)
    def test_comment_3(self):
        c = self.tpf['This is some written text']
        eq_(0, len(c.childs))
        eq_(8, c.lineno)

    def test_access_in_subprojects(self):
        p = self.tpf['One Project:']
        eq_(p['- Another'], self.tpf['- Another'])

    @raises(KeyError)
    def test_access_stays_in_subprojects(self):
        self.tpf['One Project:']['- Year!']

    @raises(KeyError)
    def test_access_to_not_existing(self):
        self.tpf['This does not exist!']

# End: Access Element by Text }}}

# Timeline Tests  {{{
class _CreateTimelineBase(unittest.TestCase):
    def setUp(self):
        self.tpf = TaskPaperFile(self.text)
        self.timeline = extract_timeline(self.tpf, dt.date(2011, 04, 01))

    def runTest(self):
        eq_(self.wanted, str(self.timeline))

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
# Logbook Tests  {{{
class _CreateLogbookBase(_TPFBaseTest):
    def setUp(self):
        _TPFBaseTest.setUp(self)
        self.tpf = TaskPaperFile(self.text)
        self.logbook = TaskPaperFile(self.logbook_text)

    def runTest(self):
        new_tpf, new_logbook = log_finished(
            self.tpf, self.logbook, dt.date(2011, 04, 03)
        )
        eq_(self.wanted, str(new_tpf))
        eq_(self.wanted_logbook, str(new_logbook))

class TestLogBook_SimpleExample_NoDate(_CreateLogbookBase):
    text = \
"""My Project:
	- This ain't
	- This task is over @done @home
	- This ain't either
"""
    wanted = \
"""My Project:
	- This ain't
	- This ain't either
"""
    logbook_text = \
"""Friday, 01. April 2011:
	- This was already done @home @what
"""
    wanted_logbook = \
"""Sunday, 03. April 2011:
	- My Project • This task is over @done @home

Friday, 01. April 2011:
	- This was already done @home @what
"""

class TestLogBook_SimpleExample_WithDate(_CreateLogbookBase):
    text = \
"""My Project:
	- This ain't
	- This task is over @done(2011-05-12) @blah
	- This task also @home @done(2011-03-30)

My Other Project:
	- Nothing is done for this
"""
    wanted = \
"""My Project:
	- This ain't

My Other Project:
	- Nothing is done for this
"""
    logbook_text = \
"""Thursday, 12. May 2011:
	- Long, Long done @done

Tuesday, 12. April 2011:
	- This is good

Tuesday, 01. March 2011:
	- This was already done @home @what
"""
    wanted_logbook = \
"""Thursday, 12. May 2011:
	- Long, Long done @done
	- My Project • This task is over @done(2011-05-12) @blah

Tuesday, 12. April 2011:
	- This is good

Wednesday, 30. March 2011:
	- My Project • This task also @home @done(2011-03-30)

Tuesday, 01. March 2011:
	- This was already done @home @what
"""

class TestLogBook_SubProjectLogging_SPNotDone(_CreateLogbookBase):
    text = \
"""My Project:
	- This is not done
	- But this is @done(2011-05-12)
	This is a subproject:
		- All @done(2011-05-11)
		- tasks @done(2011-05-11)
		- are @done(2011-05-12)
		- done @done(2011-05-12)

	- This is also not done

My Other Project:
	- Nothing is done for this
"""
    wanted = \
"""My Project:
	- This is not done
	This is a subproject:

	- This is also not done

My Other Project:
	- Nothing is done for this
"""
    logbook_text = ""
    wanted_logbook = \
"""Thursday, 12. May 2011:
	- My Project • But this is @done(2011-05-12)
	- My Project • This is a subproject • are @done(2011-05-12)
	- My Project • This is a subproject • done @done(2011-05-12)

Wednesday, 11. May 2011:
	- My Project • This is a subproject • All @done(2011-05-11)
	- My Project • This is a subproject • tasks @done(2011-05-11)
"""


class TestLogBook_SubProjectLogging_SPIsDone(_CreateLogbookBase):
    text = \
"""My Project:
	- This is not done
	- But this is @done(2011-05-12)
	This is a subproject: @done(2011-05-11)
		- All @done(2011-05-11)
		- tasks
		- are
		- done @done(2011-05-12)

	- This is also not done

My Other Project:
	- Nothing is done for this
"""
# TODO: There should be a newline after This is not done
    wanted = \
"""My Project:
	- This is not done
	- This is also not done

My Other Project:
	- Nothing is done for this
"""
    logbook_text = ""
    wanted_logbook = \
"""Thursday, 12. May 2011:
	- My Project • But this is @done(2011-05-12)
	- My Project • This is a subproject • done @done(2011-05-12)

Wednesday, 11. May 2011:
	My Project • This is a subproject: @done(2011-05-11)
		- tasks
		- are
	- My Project • This is a subproject • All @done(2011-05-11)
"""

class TestLogBook_LogWithComment(_CreateLogbookBase):
    text = \
"""My Project:
	- This is not done
	- But this is @done(2011-05-12)
		And it has a stupid comment without a tag @done(2011-05-12)
	- This is also not done

My Other Project:
	- Nothing is done for this
"""
    wanted = \
"""My Project:
	- This is not done
	- This is also not done

My Other Project:
	- Nothing is done for this
"""
    logbook_text = ""
    wanted_logbook = \
"""Thursday, 12. May 2011:
	- My Project • But this is @done(2011-05-12)
		And it has a stupid comment without a tag @done(2011-05-12)
"""

class TestLogBook_RealLifeExample(_CreateLogbookBase):
    text = \
"Privat • Verschiedenes: \n" + \
"""	- Sabine Danke für Ihren Pulli sagen @mail @done(2011-04-08) @due(2011-04-08)
"""
    wanted = \
"""Privat • Verschiedenes:
"""
    logbook_text = ""
    wanted_logbook = \
"""Friday, 08. April 2011:
	- Privat • Verschiedenes • Sabine Danke für Ihren Pulli sagen @mail @done(2011-04-08) @due(2011-04-08)
"""
# End: Logbook Tests  }}}



#######################################
# Tests on Complete File (Read Write) #
#######################################
# Reordering of Tags  {{{
class _ReorderingOfTagsBase(_TPFBaseTest):
    def runTest(self):
        reorder_tags(self.tpf)
        eq_(self.wanted, str(self.tpf))

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


