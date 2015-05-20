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

# This module is installed at the *bottom* of the file

# TODO: Implement "sections", i.e. containers of a heading and its subelements
#       and subheadings. Sections can thus be nested.
#       Make it possible to disable them.
#       In HTML sections should be enclosed in <div> tags
#       Perhaps implement them only when converting to HTML


class Marks(langmark.elements.Marks):
    HEADING1ALT_START = re.compile(r'^\={3,}[ \t]*\n', flags=re.MULTILINE)
    HEADING1ALT_END = re.compile(r'\n(\={3,}[ \t]*)?\n', flags=re.MULTILINE)
    HEADING2ALT_START = re.compile(r'^\-{3,}[ \t]*\n', flags=re.MULTILINE)
    HEADING2ALT_END = re.compile(r'\n([\=\-]{3,}[ \t]*)?\n',
                                                            flags=re.MULTILINE)
    HEADING1_START = re.compile(r'^\={1}[ \t]*(?![\= \t\n])',
                                flags=re.MULTILINE)
    HEADING2_START = re.compile(r'^\={2}[ \t]*(?![\= \t\n])',
                                flags=re.MULTILINE)
    HEADING3_START = re.compile(r'^\={3}[ \t]*(?![\= \t\n])',
                                flags=re.MULTILINE)
    HEADING4_START = re.compile(r'^\={4}[ \t]*(?![\= \t\n])',
                                flags=re.MULTILINE)
    HEADING5_START = re.compile(r'^\={5}[ \t]*(?![\= \t\n])',
                                flags=re.MULTILINE)
    HEADING6_START = re.compile(r'^\={6}[ \t]*(?![\= \t\n])',
                                flags=re.MULTILINE)


class Heading1Alt(langmark.elements._BlockElementHostingInlineStrip):
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
    HTML_TAGS = ('<h1>', '</h1>')

    @property
    def tree_bindings(self):
        return {Marks.HEADING1ALT_END: self.close}

    @property
    def recursive_close_marks(self):
        return [Marks.HEADING1ALT_END, ]


class Heading2Alt(langmark.elements._BlockElementHostingInlineStrip):
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
    # TODO: Try to recognize headings with only equal signs below:
    #
    #     Title
    #     =====
    #
    HTML_TAGS = ('<h2>', '</h2>')

    @property
    def tree_bindings(self):
        return {Marks.HEADING2ALT_END: self.close}

    @property
    def recursive_close_marks(self):
        return [Marks.HEADING2ALT_END, ]


class _SimpleHeading(langmark.elements._BlockElementHostingInlineStrip):
    @property
    def tree_bindings(self):
        return {Marks.LINE_BREAK: self.close}

    @property
    def recursive_close_marks(self):
        return [Marks.LINE_BREAK, ]


class Heading1(_SimpleHeading):
    """
    A level-1 heading (one-line syntax).::

        === Title

    There must be one space between the equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h1>', '</h1>')


class Heading2(_SimpleHeading):
    """
    A level-2 heading (one-line syntax).::

        === Title

    There must be one space between the second equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h2>', '</h2>')


class Heading3(_SimpleHeading):
    """
    A level-3 heading.::

        === Title

    There must be one space between the third equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h3>', '</h3>')


class Heading4(_SimpleHeading):
    """
    A level-4 heading.::

        ==== Title

    There must be one space between the fourth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h4>', '</h4>')


class Heading5(_SimpleHeading):
    """
    A level-5 heading.::

        ===== Title

    There must be one space between the fifth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h5>', '</h5>')


class Heading6(_SimpleHeading):
    """
    A level-6 heading.::

        ====== Title

    There must be one space between the sixth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h6>', '</h6>')

langmark.ADDITIONAL_ROOT_ELEMENTS.update({Marks.HEADING1ALT_START: Heading1Alt,
                                          Marks.HEADING2ALT_START: Heading2Alt,
                                          Marks.HEADING1_START: Heading1,
                                          Marks.HEADING2_START: Heading2,
                                          Marks.HEADING3_START: Heading3,
                                          Marks.HEADING4_START: Heading4,
                                          Marks.HEADING5_START: Heading5,
                                          Marks.HEADING6_START: Heading6})
