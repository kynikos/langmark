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

from . import (marks, elements)
from .base import RawText
from .factories import _ElementFactory
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class FormattableCode(elements._InlineElementContainingInline):
    """
    Inline formattable monospace text::

        |code|
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple('|')
    HTML_TAGS = ('<code>', '</code>')


class PlainCode(elements._InlineElementContainingHtmlText):
    """
    Inline preformatted monospace text::

        #code#
    """
    INLINE_MARK = marks._InlineMarkNonEscapableSimple('#')
    HTML_TAGS = ('<code>', '</code>')


class PlainText(elements._InlineElementContainingRawText):
    """
    Inline plain, unescaped text::

        \text\
    """
    INLINE_MARK = marks._InlineMarkNonEscapableSimple('\\')
    HTML_TAGS = ('<span>', '</span>')


class FormattableCodeBlock(elements._BlockElementContainingInline_LineMarks):
    """
    A block of formattable monospace text::

        |||
        Formatted code
        |||
    """
    HTML_TAGS = ('<pre>', '</pre>')


class PlainCodeBlock(elements._BlockElementContainingText_LineMarks):
    """
    A block of preformatted monospace text::

        ###
        Plain code
        ###
    """
    HTML_TAGS = ('<pre>', '</pre>')


class PlainTextBlock(elements._BlockElementContainingRaw_LineMarks):
    """
    A block of plain, unescaped text::

        \\\
        Plain text
        \\\
    """
    HTML_TAGS = ('<div>', '</div>')


class CodeElements(_ElementFactory):
    """
    Factory for code elements.
    """
    TEST_START_LINES = 1
    ELEMENTS = {
        FormattableCodeBlock: marks.BlockMarkSimple('|'),
        PlainCodeBlock: marks.BlockMarkSimple('#'),
        PlainTextBlock: marks.BlockMarkSimple('\\'),
    }

    def _do_make_element(self, langmark, parent, lines):
        for Element in self.ELEMENTS:
            mark = self.ELEMENTS[Element]
            match = mark.start.fullmatch(lines[0])
            if match:
                break
        else:
            raise _BlockElementStartNotMatched()
        end_mark = mark.make_end_mark(match)
        indentation_external = indentation_internal = \
                        RawText.compute_equivalent_indentation(match.group(1))
        element = Element(langmark, parent, indentation_external,
                          indentation_internal, ())
        element.set_end_mark(end_mark)
        return element
