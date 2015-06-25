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
from .base import RawText
from .factories import _BlockNotIndentedElementFactory
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class FormattableCodeInline(elements._InlineElementContainingInline):
    """
    Inline formattable monospace text::

        |code|
    """
    INLINE_MARK = marks._InlineMarkEscapableSimple('|')
    HTML_TAGS = ('<code>', '</code>')


class PlainCodeInline(elements._InlineElementContainingHtmlText):
    """
    Inline preformatted monospace text::

        #code#
    """
    INLINE_MARK = marks._InlineMarkNonEscapableSimple('#')
    HTML_TAGS = ('<code>', '</code>')


class PlainTextInline(elements._InlineElementContainingRawText):
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


class FormattableCodeBlockIndented(
                            elements._BlockElementContainingInline_Indented):
    """
    A block of formattable monospace text::

        Formatted code
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


class PlainCodeBlockIndented(elements._BlockElementContainingText_Indented):
    """
    A block of preformatted monospace text::

        Plain code
    """
    HTML_TAGS = ('<pre>', '</pre>')


class PlainTextBlock(elements._BlockElementContainingRaw_LineMarks):
    """
    A block of plain, unescaped text::

        \\\
        Plain text
        \\\
    """
    pass


class CodeElements(_BlockNotIndentedElementFactory):
    """
    Factory for code elements.
    """
    TEST_START_LINES = 1
    ELEMENTS = {
        FormattableCodeBlock: marks.BlockMarkSimple('|'),
        PlainCodeBlock: marks.BlockMarkSimple('#'),
        PlainTextBlock: marks.BlockMarkSimple('\\'),
    }

    def _find_equivalent_indentation(self, langmark_, lines):
        for Element in self.ELEMENTS:
            mark = self.ELEMENTS[Element]
            match = mark.start.fullmatch(lines[0])
            if match:
                break
        else:
            raise _BlockElementStartNotMatched()
        indentation = RawText.compute_equivalent_indentation(match.group(1))
        return (indentation, (match, ), Element)

    def _do_find_element(self, langmark_, parent, lines, indentation, matches,
                         Element):
        mark = self.ELEMENTS[Element]
        element = Element(langmark_, parent, indentation, indentation, ())
        element.set_end_mark(mark.make_end_mark(matches[0]))
        return element
