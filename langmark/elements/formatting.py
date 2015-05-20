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


class Marks(langmark.elements.Marks):
    EMPHASIS = re.compile(r'\'\'')
    STRONG = re.compile(r'\*\*')
    SUPERSCRIPT = re.compile(r'\^\^')
    SUBSCRIPT = re.compile(r',,')
    SMALL = re.compile(r';;')
    STRIKETHROUGH = re.compile(r'~~')


class Emphasis(langmark.elements._InlineElementContainingInline):
    """
    Emphasized text (usually rendered with italic formatting).::

        ''emphasized''
    """
    START_MARK = Marks.EMPHASIS
    END_MARK = Marks.EMPHASIS
    HTML_TAGS = ('<em>', '</em>')


class Strong(langmark.elements._InlineElementContainingInline):
    """
    Important text (usually rendered with bold formatting).::

        **strong**
    """
    START_MARK = Marks.STRONG
    END_MARK = Marks.STRONG
    HTML_TAGS = ('<strong>', '</strong>')


class Superscript(langmark.elements._InlineElementContainingInline):
    """
    Superscript text.::

        ^^superscript^^
    """
    START_MARK = Marks.SUPERSCRIPT
    END_MARK = Marks.SUPERSCRIPT
    HTML_TAGS = ('<sup>', '</sup>')


class Subscript(langmark.elements._InlineElementContainingInline):
    """
    Subscript text.::

        **subscript**
    """
    START_MARK = Marks.SUBSCRIPT
    END_MARK = Marks.SUBSCRIPT
    HTML_TAGS = ('<sub>', '</sub>')


class Small(langmark.elements._InlineElementContainingInline):
    """
    Small text.::

        **subscript**
    """
    START_MARK = Marks.SMALL
    END_MARK = Marks.SMALL
    HTML_TAGS = ('<small>', '</small>')


class Strikethrough(langmark.elements._InlineElementContainingInline):
    """
    Strikethrough text.::

        **subscript**
    """
    START_MARK = Marks.STRIKETHROUGH
    END_MARK = Marks.STRIKETHROUGH
    HTML_TAGS = ('<del>', '</del>')
