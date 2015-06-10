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
from . import (marks, elements)
from .base import RawText
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


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
    INLINE_MARK = marks._InlineMarkSelfClosed(
                                    r'</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>')

    def __init__(self, langmark, parent, inline_parser, parsed_text,
                 start_mark, is_element_start):
        elements._Element.__init__(self, langmark, parent)
        self.children.append(RawText(start_mark.group()))
        self.parent.take_inline_control()

    def take_inline_control(self):
        pass

    def convert_to_html(self):
        return self.children[0].get_raw_text()


class BlockMarkHTML(marks._BlockMarkFactory):
    """
    A simple sequence of the same character possibly only followed by
    whitespace characters.
    """
    # TODO: Recognize self-closed tags (excluded at the moment)
    START = re.compile(r'^([ \t]*)<(([a-zA-Z][a-zA-Z0-9]*)'
                       r'(?:[ \t][^>]*[^>/]|[ \t]*))>[ \t]*\n')
    END = r'</{escaped_tag}>[ \t]*\n'

    def __init__(self):
        self.start = self.START

    def make_end_mark(self, start_match):
        return re.compile(self.END.format(escaped_tag=re.escape(
                                                        start_match.group(3))))


class HTMLBlockTag(elements._BlockElementContainingInline):
    """
    Block HTML tag::

        <tag attribute="value">
        </tag>

        <tag attribute="value" />
    """
    # TODO: Instantiate only for actual HTML block elements (no inline/span)
    TEST_START_LINES = 1
    TEST_END_LINES = 1
    BLOCK_MARK = BlockMarkHTML()
    HTML_TAG_START = '<{tag}>'
    HTML_TAG_END = '</{tag}>'

    def check_element_start(self, lines):
        match = self.BLOCK_MARK.start.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        self.htlm_tags = (self.HTML_TAG_START.format(tag=match.group(2)),
                          self.HTML_TAG_END.format(tag=match.group(3)))
        self.end_mark = self.BLOCK_MARK.make_end_mark(match)
        return (match.group(1), ())

    def _parse_initial_lines(self, lines):
        pass

    def check_element_end(self, lines):
        if self.end_mark.fullmatch(lines[0]):
            raise _BlockElementEndConsumed()

    def convert_to_html(self):
        # This method is overriding the superclass' one
        html = self._trim_last_break(''.join(
                        child.convert_to_html() for child in self.children))
        return html.join(self.htlm_tags)
