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
from langmark import elements

# TODO: Implement "sections", i.e. containers of a heading and its subelements
#       and subheadings. Sections can thus be nested.
#       Make it possible to disable them.
#       In HTML sections should be enclosed in <div> tags
#       Perhaps implement them only when converting to HTML
# TODO: Allow normal "= H1" and "== H2" headings, maybe optionally?

# INSTALLER is defined at the *bottom* of the module
INSTALLER = None


class Marks(elements.Marks):
    HEADING1_START = re.compile(r'^\=+ *\n', flags=re.MULTILINE)
    HEADING1_END = re.compile(r'\n\=+ *\n', flags=re.MULTILINE)
    HEADING2_START = re.compile(r'^\-+ *\n', flags=re.MULTILINE)
    HEADING2_END = re.compile(r'\n\=+ *\n', flags=re.MULTILINE)
    HEADING3_START = re.compile(r'^\={3} *(?![ \=\n])', flags=re.MULTILINE)
    HEADING4_START = re.compile(r'^\={4} *(?![ \=\n])', flags=re.MULTILINE)
    HEADING5_START = re.compile(r'^\={5} *(?![ \=\n])', flags=re.MULTILINE)
    HEADING6_START = re.compile(r'^\={6} *(?![ \=\n])', flags=re.MULTILINE)


class _Heading(elements._TreeElement):
    def _handle_headingend(self, event):
        self.children.append(event.parsed_text)
        self.parent.take_control()


class Heading1(_Heading):
    """
    A level-1 heading.::

        =====
        Title
        =====

    The first and third lines can be made of any number of equal signs, but no
    other characters. The second line is taken literally as the title from the
    start of the line to the line break. The heading must have an empty line
    below itself.
    """
    HTML_TAGS = ('<h1>', '</h1>')

    def init_bindings(self):
        return {Marks.HEADING1_END: self._handle_headingend}


class Heading2(_Heading):
    """
    A level-2 heading.::

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

    def init_bindings(self):
        return {Marks.HEADING2_END: self._handle_headingend}


class _Heading3456(_Heading):
    def init_bindings(self):
        return {Marks.LINE_BREAK: self._handle_headingend}


class Heading3(_Heading3456):
    """
    A level-3 heading.::

        === Title

    There must be one space between the third equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h3>', '</h3>')


class Heading4(_Heading3456):
    """
    A level-4 heading.::

        ==== Title

    There must be one space between the fourth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h4>', '</h4>')


class Heading5(_Heading3456):
    """
    A level-5 heading.::

        ===== Title

    There must be one space between the fifth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h5>', '</h5>')


class Heading6(_Heading3456):
    """
    A level-6 heading.::

        ====== Title

    There must be one space between the sixth equal sign and the title. The
    rest of the line is taken literally as the title until the line break. The
    heading must have an empty line below itself.
    """
    HTML_TAGS = ('<h6>', '</h6>')

INSTALLER = {Marks.HEADING1_START: Heading1,
             Marks.HEADING2_START: Heading2,
             Marks.HEADING3_START: Heading3,
             Marks.HEADING4_START: Heading4,
             Marks.HEADING5_START: Heading5,
             Marks.HEADING6_START: Heading6}
