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


class FormattableCode(base._InlineElementContainingInline):
    """
    Inline formattable monospace text::

        |code|
    """
    INLINE_MARK = marks._InlineMarkEscapable('|')
    HTML_TAGS = ('<code>', '</code>')


class PlainCode(base._InlineElementContainingHtmlText):
    """
    Inline preformatted monospace text::

        #code#
    """
    INLINE_MARK = marks._InlineMarkNonEscapable('#')
    HTML_TAGS = ('<code>', '</code>')


class PlainText(base._InlineElementContainingRawText):
    """
    Inline plain, unescaped text::

        \text\
    """
    INLINE_MARK = marks._InlineMarkNonEscapable('\\')
    HTML_TAGS = ('<span>', '</span>')


class FormattableCodeBlock(base._BlockElementContainingInline_LineMarks):
    """
    A block of formattable monospace text::

        |||
        Formatted code
        |||
    """
    BLOCK_MARK = marks.BlockMarkSimple('|')
    HTML_TAGS = ('<pre>', '</pre>')


class PlainCodeBlock(base._BlockElementContainingText_LineMarks):
    """
    A block of preformatted monospace text::

        ###
        Plain code
        ###
    """
    BLOCK_MARK = marks.BlockMarkSimple('#')
    HTML_TAGS = ('<pre>', '</pre>')


class PlainTextBlock(base._BlockElementContainingRaw_LineMarks):
    """
    A block of plain, unescaped text::

        \\\
        Plain text
        \\\
    """
    BLOCK_MARK = marks.BlockMarkSimple('\\')
    HTML_TAGS = ('<div>', '</div>')
