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
from .base import RawText, Configuration
from .factories import _BlockNotIndentedElementFactory
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class HTMLElements(_BlockNotIndentedElementFactory):
    """
    Factory for HTML block elements.
    """
    TEST_START_LINES = 2
    # Trying to recognize an element as a container (i.e. associating a start
    #  and end tag and a content in between) is too complex for the purpose of
    #  this application, also because some tags need a closing tag, others are
    #  self-closed, some can stay inside a paragraph, others can't etc.
    #  It must be up to the editor to use the tags correctly
    # TODO: Instantiate only for actual HTML block elements (no inline/span)
    HTML_RE = r'<(?:\!--.*?|(!doctype|/?[a-z][a-z0-9]*)(?:\s[^>]*|/)?>)'
    BLOCK_MARK = re.compile(HTML_RE.join((r'^([ \t]*)', r'[ \t]*\n')),
                            re.IGNORECASE)

    def _find_equivalent_indentation(self, langmark_, lines):
        match1 = Configuration.BLANK_LINE.fullmatch(lines[0])
        if not match1:
            raise _BlockElementStartNotMatched()
        match2 = self.BLOCK_MARK.fullmatch(lines[1])
        if not match2:
            raise _BlockElementStartNotMatched()
        indentation = RawText.compute_equivalent_indentation(match2.group(1))
        return (indentation, (), None)

    def _do_find_element(self, langmark_, parent, lines, indentation, matches,
                         Element):
        return HTMLBlockTag(langmark_, parent, indentation, indentation,
                            (lines[1], ))


class HTMLBlockTag(elements._BlockElementContainingRaw_EmptyLine):
    """
    Block HTML tag::

        <tag attribute="value">
        </tag>
        <tag attribute="value" />
    """
    pass


class HTMLInlineTag(elements._Element):
    """
    Inline HTML tag::

        <tag attribute="value">
        </tag>
        <tag attribute="value" />
    """
    # Trying to recognize the element as a container (i.e. associating a start
    #  and end tag and a content in between) is too complex for the purpose of
    #  this application, also because some tags need a closing tag, others are
    #  self-closed, some can stay inside a paragraph, others can't etc.
    #  It must be up to the editor to use the tags correctly
    INLINE_MARK = marks._InlineMarkStartOnly(re.compile(HTMLElements.HTML_RE,
                                                        re.IGNORECASE))

    def __init__(self, langmark_, parent, inline_parser, parsed_text,
                 start_mark, is_element_start):
        elements._Element.__init__(self, langmark_, parent)
        self.children.append(RawText(start_mark.group()))
        self.parent.take_inline_control()

    def take_inline_control(self):
        pass

    def convert_to_html(self):
        return self.children[0].get_raw_text()
