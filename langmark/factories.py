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
import langmark
from . import marks
from .base import Configuration, RawText
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
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
    Base class for content element factories.
    """
    TEST_START_LINES = None

    def make_element(self, langmark_, parent):
        try:
            lines = parent.read_lines(self.TEST_START_LINES)
        except _EndOfFile:
            # Don't just process the exception here because other elements may
            #  require a lesser number of test start lines, hence not raising
            #  _EndOfFile/StopIteration
            pass
        else:
            try:
                # Finding the element is the actual exception in this algorithm
                # Note how _do_make_element itself can raise other exceptions
                raise _BlockElementStartMatched(self._do_make_element(
                                                    langmark_, parent, lines))
            except _BlockElementStartNotMatched:
                pass
        langmark_.stream.rewind_buffer()
        return False

    def _do_make_element(self, langmark_, parent, lines):
        raise NotImplementedError()


class _MetaDataElementFactory(_ElementFactory):
    """
    Base class for metadata element factories.
    """
    METADATA = None

    def _do_make_element(self, langmark_, parent, lines):
        # TODO: Support multiline metadata (using indentation for the
        #       continuation lines)
        self.process_match(langmark_, self.METADATA.fullmatch(lines[0]))
        raise _BlockElementStartConsumed()

    def process_match(self, langmark_, match):
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
            langmark.elements._BlockElementContainingBlock.INSTALLED_BLOCK_FACTORIES.remove(
                                                                        self)
            langmark_.stream.rewind_buffer()
            # Add an empty line to make it possible to recognize elements that
            # start with an empty line (e.g. headings)
            langmark_.stream.rewind_lines('\n')


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

    def _find_equivalent_indentation(self, langmark, lines):
        raise NotImplementedError()

    def _find_element(self, langmark, parent, lines, indentation, matches,
                      Element):
        raise NotImplementedError()


class IndentedElements(_BlockElementFactory):
    """
    Factory for elements based on indentation.
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


class _BlockNotIndentedElementFactory(_BlockElementFactory):
    """
    Factory for elements based on marks.
    """
    def _find_element(self, langmark, parent, lines, indentation, matches,
                      Element):
        # This allows escaping with an initial space
        if indentation > parent.indentation_internal:
            raise _BlockElementStartNotMatched()
        return self._do_find_element(langmark, parent, lines, indentation,
                                     matches, Element)

    def _do_find_element(self, langmark, parent, lines, indentation, matches,
                         Element):
        raise NotImplementedError()


class ParagraphFactory(_BaseFactory):
    """
    Factory for paragraph elements.
    """
    def make_element(self, langmark_, parent):
        # This can raise _EndOfFile for example when a document ends with a
        #  metadata element, but don't process the exception here
        lines = parent.read_lines(1)
        line = lines[0]
        if Configuration.BLANK_LINE.fullmatch(line):
            raise _BlockElementStartNotMatched()
        indentationtext = Configuration.INDENTATION.match(line).group()
        # TODO: The equivalent indentation has already been computed at
        #       least once in IndentedElements: finding a way to reuse it
        #       would make things a little faster
        indentation = RawText.compute_equivalent_indentation(indentationtext)
        parent = self._find_correct_parent(parent, indentation)
        return langmark.elements.Paragraph(langmark_, parent,
                                           # Don't use 'indentation' here,
                                           #  because it may contain the
                                           #  leading escaping space
                                           parent.indentation_internal,
                                           parent.indentation_internal, lines)


class HorizontalRules(_BlockNotIndentedElementFactory):
    """
    Factory for horizontal rule elements.
    """
    TEST_START_LINES = 1
    # There can't be conflicts with headings if the factory is inserted after
    #  the headings factory in BLOCK_FACTORIES
    BLOCK_MARK = marks.BlockMarkRepeat('-', '_', '~', '=', '*', '+')

    def _find_equivalent_indentation(self, langmark_, lines):
        match = self.BLOCK_MARK.mark.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        indentation = RawText.compute_equivalent_indentation(match.group(1))
        return (indentation, (), None)

    def _do_find_element(self, langmark_, parent, lines, indentation, matches,
                         Element):
        return langmark.elements.HorizontalRule(langmark_, parent, indentation,
                                                indentation, ())
