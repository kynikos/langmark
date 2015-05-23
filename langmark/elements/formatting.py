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
    EMPHASIS = '_'
    STRONG = '*'
    SUPERSCRIPT = '^'
    SUBSCRIPT = ';'
    SMALL = ':'
    STRIKETHROUGH = '~'


class Emphasis(langmark.elements._InlineElementContainingInline):
    """
    Emphasized text (usually rendered with italic formatting).::

        _emphasized_
    """
    MARK = Marks.EMPHASIS
    HTML_TAGS = ('<em>', '</em>')


class Strong(langmark.elements._InlineElementContainingInline):
    """
    Important text (usually rendered with bold formatting).::

        *strong*
    """
    MARK = Marks.STRONG
    HTML_TAGS = ('<strong>', '</strong>')


class Superscript(langmark.elements._InlineElementContainingInline):
    """
    Superscript text.::

        ^superscript^
    """
    MARK = Marks.SUPERSCRIPT
    HTML_TAGS = ('<sup>', '</sup>')


class Subscript(langmark.elements._InlineElementContainingInline):
    """
    Subscript text.::

        ;subscript;
    """
    MARK = Marks.SUBSCRIPT
    HTML_TAGS = ('<sub>', '</sub>')


class Small(langmark.elements._InlineElementContainingInline):
    """
    Small text.::

        :small:
    """
    MARK = Marks.SMALL
    HTML_TAGS = ('<small>', '</small>')


class Strikethrough(langmark.elements._InlineElementContainingInline):
    """
    Strikethrough text.::

        ~strikethrough~
    """
    MARK = Marks.STRIKETHROUGH
    HTML_TAGS = ('<del>', '</del>')
