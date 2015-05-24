# Langmark - A hypertext markup language with a powerful and extensible parser.
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
import langmark

# TODO: Implement "sections", i.e. containers of a heading and its subelements
#       and subheadings. Sections can thus be nested.
#       Make it possible to disable them.
#       In HTML sections should be enclosed in <div> tags
#       Perhaps implement them only when converting to HTML


class _SimpleHeading(langmark.elements._BlockElementContainingInline):
    """
    A block element, containing inline elements, that can only span one line
    and is identified by a prefix.

    START_MARK's first capturing group will be used as the element content.
    """
    START_RE = (r'^()\={{{level}}}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                 '[ \t]*\=*[ \t]*\n')
    START_MARK = None

    def check_element_start(self, line):
        match = self.START_MARK.match(line)
        if not match:
            raise langmark.elements._BlockElementStartNotMatched(line)
        indent = len(match.group(1))
        return (indent, indent, match.group(2))

    def check_element_end(self, line):
        if self.rawtext:
            raise langmark.elements._BlockElementEndNotConsumed(line)


class _ComplexHeading(langmark.elements._BlockElementContainingInline):
    """
    A block element, containing inline elements, that starts with a full-line
    mark and ends with an optional full-line mark.
    """
    ONELINE_MARK = None
    START_MARK = None
    END_MARK = None

    def check_element_start(self, line):
        match = self.ONELINE_MARK.match(line)
        if match:
            indent = len(match.group(1))
            indented_line = match.group(2)

        elif langmark.elements._Regexs.BLANK_LINE.fullmatch(line):
            line2 = self.read_next_line()
            line3 = self.read_next_line()
            match3 = self.END_MARK.fullmatch(line3)
            if not match3:
                raise langmark.elements._BlockElementStartNotMatched(line,
                                                                line2, line3)
            indent = len(match3.group(1))
            indented_line = line2

        else:
            match1 = self.START_MARK.fullmatch(line)
            if not match1:
                raise langmark.elements._BlockElementStartNotMatched(line)
            line2 = self.read_next_line()
            line3 = self.read_next_line()
            match3 = self.END_MARK.fullmatch(line3)
            if not match3:
                raise langmark.elements._BlockElementStartNotMatched(line,
                                                                line2, line3)
            indent = len(match1.group(1))
            indented_line = line2

        return (indent, indent, indented_line)

    def check_element_end(self, line):
        if self.rawtext:
            raise langmark.elements._BlockElementEndNotConsumed(line)


class Heading1(_ComplexHeading):
    """
    A level-1 heading.::

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
    ONELINE_MARK = re.compile(_SimpleHeading.START_RE.format(level='1'))
    START_MARK = re.compile(r'^()\={3,}[ \t]*\n')
    END_MARK = re.compile(r'^()\=+[ \t]*\n')
    HTML_TAGS = ('<h1>', '</h1>')


class Heading2(_ComplexHeading):
    """
    A level-2 heading.::

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
    ONELINE_MARK = re.compile(_SimpleHeading.START_RE.format(level='2'))
    START_MARK = re.compile(r'^()[\=\-]{3,}[ \t]*\n')
    END_MARK = re.compile(r'^()[\=\-]+[ \t]*\n')
    HTML_TAGS = ('<h2>', '</h2>')


class Heading3(_SimpleHeading):
    """
    A level-3 heading.::

        === Title

    There must be one space between the third equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = re.compile(_SimpleHeading.START_RE.format(level='3'))
    HTML_TAGS = ('<h3>', '</h3>')


class Heading4(_SimpleHeading):
    """
    A level-4 heading.::

        ==== Title

    There must be one space between the fourth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = re.compile(_SimpleHeading.START_RE.format(level='4'))
    HTML_TAGS = ('<h4>', '</h4>')


class Heading5(_SimpleHeading):
    """
    A level-5 heading.::

        ===== Title

    There must be one space between the fifth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = re.compile(_SimpleHeading.START_RE.format(level='5'))
    HTML_TAGS = ('<h5>', '</h5>')


class Heading6(_SimpleHeading):
    """
    A level-6 heading.::

        ====== Title

    There must be one space between the sixth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = re.compile(_SimpleHeading.START_RE.format(level='6,'))
    HTML_TAGS = ('<h6>', '</h6>')
