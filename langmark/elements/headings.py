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


class Marks(langmark.elements.Marks):
    HEADING1ALT_START = re.compile(r'^()\={3,}[ \t]*\n')
    HEADING1ALT_END = re.compile(r'^()\=*[ \t]*\n')
    HEADING2ALT_START = re.compile(r'^()[\=\-]{3,}[ \t]*\n')
    HEADING2ALT_END = re.compile(r'^()[\=\-]*[ \t]*\n')
    HEADING1 = re.compile(r'^()\={1}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                           '[ \t]*\=*[ \t]*\n')
    HEADING2 = re.compile(r'^()\={2}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                           '[ \t]*\=*[ \t]*\n')
    HEADING5 = re.compile(r'^()\={5}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                           '[ \t]*\=*[ \t]*\n')
    HEADING3 = re.compile(r'^()\={3}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                           '[ \t]*\=*[ \t]*\n')
    HEADING4 = re.compile(r'^()\={4}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                           '[ \t]*\=*[ \t]*\n')
    HEADING6 = re.compile(r'^()\={6,}[ \t]*((?:(?<=[ \t])\=|[^\=]).*?)'
                           '[ \t]*\=*[ \t]*\n')


class Heading1Alt(
        langmark.elements._BlockElementContainingInline_LineMarkOptionalEnd):
    """
    A level-1 heading (multiline syntax).::

        =====
        Title
        =====

    The first and third lines can be made of any number of equal signs, but no
    other characters. The second line is taken literally as the title from the
    start of the line to the line break. The heading must have an empty line
    below itself.
    """
    START_MARK = Marks.HEADING1ALT_START
    END_MARK = Marks.HEADING1ALT_END
    HTML_TAGS = ('<h1>', '</h1>')


class Heading2Alt(
        langmark.elements._BlockElementContainingInline_LineMarkOptionalEnd):
    """
    A level-2 heading (multiline syntax).::

        -----
        Title
        =====

    The first line can be made of any number of dash signs, but no other
    characters. The third line can be made of any number of equal signs, but no
    other characters. The second line is taken literally as the title from the
    start of the line to the line break. The heading must have an empty line
    below itself.
    """
    # TODO: Try to recognize headings with only equal signs below (maybe
    #       reading the preceding empty line):
    #
    #     Title
    #     =====
    #
    START_MARK = Marks.HEADING2ALT_START
    END_MARK = Marks.HEADING2ALT_END
    HTML_TAGS = ('<h2>', '</h2>')


class Heading1(langmark.elements._BlockElementContainingInline_OneLine):
    """
    A level-1 heading (one-line syntax).::

        === Title

    There must be one space between the equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = Marks.HEADING1
    HTML_TAGS = ('<h1>', '</h1>')


class Heading2(langmark.elements._BlockElementContainingInline_OneLine):
    """
    A level-2 heading (one-line syntax).::

        === Title

    There must be one space between the second equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = Marks.HEADING2
    HTML_TAGS = ('<h2>', '</h2>')


class Heading3(langmark.elements._BlockElementContainingInline_OneLine):
    """
    A level-3 heading.::

        === Title

    There must be one space between the third equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = Marks.HEADING3
    HTML_TAGS = ('<h3>', '</h3>')


class Heading4(langmark.elements._BlockElementContainingInline_OneLine):
    """
    A level-4 heading.::

        ==== Title

    There must be one space between the fourth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = Marks.HEADING4
    HTML_TAGS = ('<h4>', '</h4>')


class Heading5(langmark.elements._BlockElementContainingInline_OneLine):
    """
    A level-5 heading.::

        ===== Title

    There must be one space between the fifth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = Marks.HEADING5
    HTML_TAGS = ('<h5>', '</h5>')


class Heading6(langmark.elements._BlockElementContainingInline_OneLine):
    """
    A level-6 heading.::

        ====== Title

    There must be one space between the sixth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    START_MARK = Marks.HEADING6
    HTML_TAGS = ('<h6>', '</h6>')
