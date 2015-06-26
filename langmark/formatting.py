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

from . import (marks, elements)


class Emphasis(elements._InlineElementContainingInline):
    """
    Emphasized text (usually rendered with italic formatting)::

        _emphasized_
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple('_')
    HTML_TAGS = ('<em>', '</em>')


class Strong(elements._InlineElementContainingInline):
    """
    Important text (usually rendered with bold formatting)::

        *strong*
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple('*')
    HTML_TAGS = ('<strong>', '</strong>')


class Superscript(elements._InlineElementContainingInline):
    """
    Superscript text::

        ^^superscript^^
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple2('^')
    HTML_TAGS = ('<sup>', '</sup>')


class Subscript(elements._InlineElementContainingInline):
    """
    Subscript text::

        ,,subscript,,
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple2(',')
    HTML_TAGS = ('<sub>', '</sub>')


class Small(elements._InlineElementContainingInline):
    """
    Small text::

        ::small::
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple2(':')
    HTML_TAGS = ('<small>', '</small>')


class Strikethrough(elements._InlineElementContainingInline):
    """
    Strikethrough text::

        ~~strikethrough~~
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple2('~')
    HTML_TAGS = ('<del>', '</del>')
