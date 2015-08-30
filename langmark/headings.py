# Langmark - A powerful and extensible lightweight markup language.
# Copyright (C) 2015 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Langmark.
#
# Langmark is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Langmark is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Langmark.  If not, see <http://www.gnu.org/licenses/>.

import re
from . import elements
from .base import Configuration
from .factories import _BlockNotIndentedElementFactory
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)

# TODO: Implement "sections", i.e. containers of a heading and its subelements
#       and subheadings. Sections can thus be nested.
#       Make it possible to disable them.
#       In HTML sections should be enclosed in <div> tags
#       Perhaps implement them only when converting to HTML
#       Also give a way to end a section without starting another, e.g.:
#
#       == Parent ==
#
#       Parent text.
#
#       === Child ===
#
#       Child text.
#
#       =============
#
#       Continued parent text.
#


class _Heading(elements._BlockElementContainingInline):
    """
    Base class for heading elements.
    """
    TEST_END_LINES = 0

    def _process_initial_lines(self, lines):
        self._add_raw_first_line(lines[0])

    def check_element_end(self, lines):
        raise _BlockElementEndConsumed()


class Heading1(_Heading):
    """
    A level-1 heading::

        = Title

    There must be one space between the equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.

        Title
        =====

        =====
        Title
        =====

    The first and third lines can be made of any number of equal signs, but no
    other characters. The second line is taken literally as the title from the
    start of the line to the line break. The heading must have an empty line
    below itself.
    """
    HTML_TAGS = ('<h1>', '</h1>')


class Heading2(_Heading):
    """
    A level-2 heading::

        == Title

    There must be one space between the second equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.

        Title
        -----

        -----
        Title
        =====

    The first line can be made of any number of dash signs, but no other
    characters. The third line can be made of any number of equal signs, but no
    other characters. The second line is taken literally as the title from the
    start of the line to the line break. The heading must have an empty line
    below itself.
    """
    HTML_TAGS = ('<h2>', '</h2>')


class Heading3(_Heading):
    """
    A level-3 heading::

        === Title

    There must be one space between the third equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h3>', '</h3>')


class Heading4(_Heading):
    """
    A level-4 heading::

        ==== Title

    There must be one space between the fourth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h4>', '</h4>')


class Heading5(_Heading):
    """
    A level-5 heading::

        ===== Title

    There must be one space between the fifth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h5>', '</h5>')


class Heading6(_Heading):
    """
    A level-6 heading::

        ====== Title

    There must be one space between the sixth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h6>', '</h6>')


class HeadingElements(_BlockNotIndentedElementFactory):
    """
    Factory for heading elements.
    """
    TEST_START_LINES = 3
    ELEMENTS = (Heading1, Heading2, Heading3, Heading4, Heading5, Heading6)
    # ONELINE_MARK's second capturing group will be used as the element
    #  content.
    ONELINE_MARK = re.compile(r'^(\=+)[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                              r'[ \t]*\=*[ \t]*\n')
    START_MARK_1 = re.compile(r'^\={3,}[ \t]*\n')
    START_MARK_2 = re.compile(r'^[\=\-]{3,}[ \t]*\n')
    TITLE_MARK = re.compile(r'^[ \t]*(.+?)[ \t]*\n')
    END_MARK_1 = re.compile(r'^\={3,}[ \t]*\n')
    END_MARK_2 = re.compile(r'^[\=\-]{3,}[ \t]*\n')

    def _find_equivalent_indentation(self, langmark_, lines):
        return (0, (), None)

    def _do_find_element(self, langmark_, parent, lines, indentation, matches,
                         Element):
        match = self.ONELINE_MARK.match(lines[0])
        if match:
            level = min(len(match.group(1)), 6)
            Element = self.ELEMENTS[level - 1]
            title = match.group(2)
            langmark_.stream.rewind_lines(lines[1], lines[2])

        elif Configuration.BLANK_LINE.fullmatch(lines[0]):
            match2 = self.TITLE_MARK.fullmatch(lines[1])
            if not match2:
                raise _BlockElementStartNotMatched()
            if self.END_MARK_1.fullmatch(lines[2]):
                Element = Heading1
            elif self.END_MARK_2.fullmatch(lines[2]):
                Element = Heading2
            else:
                raise _BlockElementStartNotMatched()
            title = match2.group(1)

        else:
            if self.START_MARK_1.fullmatch(lines[0]):
                if self.END_MARK_1.fullmatch(lines[2]):
                    Element = Heading1
                elif self.END_MARK_2.fullmatch(lines[2]):
                    Element = Heading2
                else:
                    raise _BlockElementStartNotMatched()
            elif self.START_MARK_2.fullmatch(lines[0]):
                if not self.END_MARK_2.fullmatch(lines[2]):
                    raise _BlockElementStartNotMatched()
                Element = Heading2
            else:
                raise _BlockElementStartNotMatched()
            match2 = self.TITLE_MARK.fullmatch(lines[1])
            if not match2:
                raise _BlockElementStartNotMatched()
            title = match2.group(1)

        return Element(langmark_, parent, 0, 0, (title, ))
