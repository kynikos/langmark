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

import re
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


class UnorderedListItem(elements._BlockElementContainingBlock_PrefixGrouped):
    """
    An unordered list item::

        * List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    HTML_OUTER_TAGS = ('<ul>', '</ul>')
    HTML_TAGS = ('<li>', '</li>')


class NumberedListItem(elements._BlockElementContainingBlock_PrefixGrouped):
    """
    A numbered list item::

        #. List item
        1. List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    HTML_OUTER_TAGS = ('<ol>', '</ol>')
    HTML_TAGS = ('<li>', '</li>')


class LatinListItem(elements._BlockElementContainingBlock_PrefixGrouped):
    """
    An alphabetical list item using Latin characters::

        &. List item
        a. List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    # TODO: Let customize the class name
    HTML_OUTER_TAGS = ('<ol class="langmark-latin">', '</ol>')
    HTML_TAGS = ('<li>', '</li>')


class ListElements(_BlockNotIndentedElementFactory):
    """
    Factory for list elements.
    """
    TEST_START_LINES = 1
    ELEMENTS = {
        UnorderedListItem: marks.BlockMarkPrefix(r'\*'),
        NumberedListItem: marks.BlockMarkPrefix(r'(?:[0-9]+|#)\.'),
        LatinListItem: marks.BlockMarkPrefix(r'[a-zA-Z&]\.'),
    }

    def _find_equivalent_indentation(self, langmark_, lines):
        for Element in self.ELEMENTS:
            mark = self.ELEMENTS[Element]
            match = mark.prefix.fullmatch(lines[0])
            if match:
                break
        else:
            raise _BlockElementStartNotMatched()
        indentation = RawText.compute_equivalent_indentation(match.group(1))
        return (indentation, (match, ), Element)

    def _do_find_element(self, langmark_, parent, lines, indentation, matches,
                         Element):
        external_indentation = indentation
        match = matches[0]
        internal_indentation = external_indentation + \
                        RawText.compute_equivalent_indentation(match.group(2))
        # Remove the prefix, otherwise the same block will be parsed
        #  recursively endlessly
        adapted_line = ''.join((' ' * internal_indentation, match.group(3)))
        return Element(langmark_, parent, external_indentation,
                       internal_indentation, (adapted_line, ))
