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
from .factories import _ElementFactory
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class BlockQuote(elements._BlockElementContainingBlock):
    """
    A quote block::

        > > quoted text
        > quoted text
    """
    # TODO: For the moment it's impossible to have two separate quote blocks
    #       without other elements between them
    HTML_TAGS = ('<blockquote>', '</blockquote>')


    def preprocess_inline(self, line, indentation_internal):
        # This test excludes space-escaped quote blocks
        if line.startswith('>'):
            return line[:indentation_internal].replace(
                QuoteElements.BLOCK_CHAR, ' ') + line[indentation_internal:]
        return line


class QuoteElements(_ElementFactory):
    """
    Factory for quote block elements.
    """
    TEST_START_LINES = 1
    BLOCK_CHAR = '>'
    BLOCK_MARK = marks.BlockMarkPrefixCompact(BLOCK_CHAR)

    def _do_make_element(self, langmark_, parent, lines):
        initial_parent = parent
        match = self.BLOCK_MARK.prefix.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        external_indentation = RawText.compute_equivalent_indentation(
                                                                match.group(1))
        parent = self._find_correct_parent(initial_parent,
                                                        external_indentation)
        # This allows escaping with an initial space
        if external_indentation > parent.indentation_internal:
            raise _BlockElementStartNotMatched()
        while True:
            internal_indentation = external_indentation + \
                        RawText.compute_equivalent_indentation(match.group(2))
            adapted_line = match.group().replace(self.BLOCK_CHAR, ' ', 1)
            try:
                prevsibling = parent.children[-1]
            except IndexError:
                break
            else:
                if prevsibling.__class__ is BlockQuote and \
                                            internal_indentation >= \
                                            prevsibling.indentation_internal:
                    match = self.BLOCK_MARK.prefix.fullmatch(adapted_line)
                    if not match:
                        raise _BlockElementContinue(prevsibling,
                                                    (adapted_line, ))
                    # Here is the only case that continues the loop
                else:
                    break
            external_indentation = RawText.compute_equivalent_indentation(
                                                                match.group(1))
            parent = self._find_correct_parent(initial_parent,
                                                        external_indentation)
            # This allows escaping with an initial space
            if external_indentation > parent.indentation_internal:
                raise _BlockElementContinue(parent, (adapted_line, ))
        return BlockQuote(langmark_, parent, external_indentation,
                          internal_indentation, (adapted_line, ))
