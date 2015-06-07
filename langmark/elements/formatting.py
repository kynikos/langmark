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

from . import (marks, base)


class Emphasis(base._InlineElementContainingInline):
    """
    Emphasized text (usually rendered with italic formatting)::

        _emphasized_
    """
    INLINE_MARK = marks._InlineMarkEscapable('_')
    HTML_TAGS = ('<em>', '</em>')


class Strong(base._InlineElementContainingInline):
    """
    Important text (usually rendered with bold formatting)::

        *strong*
    """
    INLINE_MARK = marks._InlineMarkEscapable('*')
    HTML_TAGS = ('<strong>', '</strong>')


class Superscript(base._InlineElementContainingInline):
    """
    Superscript text::

        ^superscript^
    """
    INLINE_MARK = marks._InlineMarkEscapable('^')
    HTML_TAGS = ('<sup>', '</sup>')


class Subscript(base._InlineElementContainingInline):
    """
    Subscript text::

        ;subscript;
    """
    INLINE_MARK = marks._InlineMarkEscapable(';')
    HTML_TAGS = ('<sub>', '</sub>')


class Small(base._InlineElementContainingInline):
    """
    Small text::

        :small:
    """
    INLINE_MARK = marks._InlineMarkEscapable(':')
    HTML_TAGS = ('<small>', '</small>')


class Strikethrough(base._InlineElementContainingInline):
    """
    Strikethrough text::

        ~strikethrough~
    """
    INLINE_MARK = marks._InlineMarkEscapable('~')
    HTML_TAGS = ('<del>', '</del>')
