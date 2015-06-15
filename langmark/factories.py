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
from .base import Configuration, RawText
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class _BaseFactory:
    """
    Base class for element factories.
    """
    def __init__(self):
        pass

    def _find_correct_parent(self, parent, indentation):
        while indentation < parent.indentation_internal:
            parent = parent.parent
        return parent


class _ElementFactory(_BaseFactory):
    """
    Base class for element factories.
    """
    TEST_START_LINES = None

    def make_element(self, langmark, parent):
        try:
            lines = langmark.stream.read_next_lines_buffered(
                                                        self.TEST_START_LINES)
        except StopIteration:
            # Don't just process the exception here because other elements may
            #  require a lesser number of test start lines, hence not raising
            #  StopIteration
            pass
        else:
            try:
                # Finding the element is the actual exception in this algorithm
                # Note how _do_make_element itself can raise other exceptions
                raise _BlockElementStartMatched(self._do_make_element(langmark,
                                                                parent, lines))
            except _BlockElementStartNotMatched:
                pass
        langmark.stream.rewind_buffer()
        return False

    def _do_make_element(self, langmark, parent, lines):
        raise NotImplementedError()


class _MetaDataElementFactory(_ElementFactory):
    """
    Base class for metadata element factories.
    """
    METADATA = None

    def _do_make_element(self, langmark, parent, lines):
        # TODO: Support multiline metadata (using indentation for the
        #       continuation lines)
        self.process_match(langmark, self.METADATA.fullmatch(lines[0]))
        raise _BlockElementStartConsumed()

    def process_match(self, langmark, match):
        raise NotImplementedError()


class HeaderElements(_MetaDataElementFactory):
    """
    Generic key/value metadata elements::

        ::key value

    Spaces between ``::`` and the key are ignored.
    The key cannot contain spaces.
    A value string is optional and is considered to start after the first
    sequence of spaces after the key string.
    """
    TEST_START_LINES = 1
    METADATA = re.compile(r'^\:\:[ \t]*(.+?)(?:[ \t]+(.+?))?[ \t]*\n')

    def process_match(self, langmark_, match):
        if match:
            langmark_.header.keys[match.group(1)] = match.group(2)
        else:
            # This is changing the size of INSTALLED_BLOCK_FACTORIES, so I
            #  can't raise _BlockElementStartNotMatched after it, because that
            #  would simply continue the for loop in
            #  _BlockElement.find_element_start, which would hence skip the
            #  next element in the list
            # Installing this class at the top of INSTALLED_BLOCK_FACTORIES
            #  makes this as efficient as continuing the loop, since no other
            #  elements are uselessly tested
            langmark.elements._BlockElement.INSTALLED_BLOCK_FACTORIES.remove(
                                                                        self)
            langmark_.stream.rewind_buffer()


class _BlockElementFactory(_ElementFactory):
    """
    Factory for block elements.
    """
    def _do_make_element(self, langmark, parent, lines):
        indentation, matches, Element = self._find_equivalent_indentation(
                                                            langmark, lines)
        parent = self._find_correct_parent(parent, indentation)
        return self._find_element(langmark, parent, lines, indentation,
                                  matches, Element)

    def _find_raw_indentation(self, langmark, lines):
        raise NotImplementedError()

    def _find_element(self, langmark, parent, lines, indentation, matches,
                      Element):
        raise NotImplementedError()


class IndentedElements(_BlockElementFactory):
    """
    Factory for indented elements.
    """
    TEST_START_LINES = 1
    INSTALLED_ELEMENTS = None

    def _find_equivalent_indentation(self, langmark, lines):
        line = lines[0]
        if Configuration.BLANK_LINE.fullmatch(line):
            raise _BlockElementStartNotMatched()
        indentation = RawText.compute_equivalent_indentation(
                                Configuration.INDENTATION.match(line).group())
        return (indentation, (), None)

    def _find_element(self, langmark, parent, lines, indentation, matches,
                      Element):
        indent_diff = indentation - parent.indentation_internal
        if indent_diff < 1:
            raise _BlockElementStartNotMatched()
        try:
            Element = self.INSTALLED_ELEMENTS[indent_diff - 1]
        except IndexError:
            indent_diff = len(self.INSTALLED_ELEMENTS)
            Element = self.INSTALLED_ELEMENTS[-1]
        # INSTALLED_ELEMENTS must support None values to ignore particular
        #  levels of indentation
        if not Element:
            raise _BlockElementStartNotMatched()
        return Element(langmark, parent, parent.indentation_internal,
                       parent.indentation_internal + indent_diff, lines)


class ParagraphFactory(_BaseFactory):
    """
    Paragraph factory class.
    """
    def make_element(self, langmark_, parent):
        try:
            lines = langmark_.stream.read_next_lines_buffered(1)
        except StopIteration:
            # This can happen for example when a document ends with a
            #  metadata element
            raise _EndOfFile()
        else:
            line = lines[0]
            if Configuration.BLANK_LINE.fullmatch(line):
                raise _BlockElementStartNotMatched()
            indentationtext = Configuration.INDENTATION.match(line).group()
            indentation = RawText.compute_equivalent_indentation(
                                                            indentationtext)
            parent = self._find_correct_parent(parent, indentation)
            return langmark.elements.Paragraph(langmark_, parent, indentation,
                                               indentation, lines)
