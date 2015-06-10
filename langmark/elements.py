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
import textparser
from .base import (Configuration, RawText)
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class _Element:
    """
    Base class for document elements.
    """
    def __init__(self, langmark, parent):
        self.langmark = langmark
        self.parent = parent
        self.children = []

    def reset_parent(self, element):
        self.parent = element

    def _rewind_check_lines_buffer(self):
        self.rewind_lines(*self.langmark.stream.lines_buffer)

    def rewind_lines(self, *lines):
        self.langmark.stream.rewind_lines(*lines)

    @staticmethod
    def _trim_last_break(text):
        if text.endswith('\n'):
            return text[:-1]
        return text

    def convert_to_html(self):
        # TODO: Convert to HTML *while* building the tree, not afterwards
        #       (use events?)
        raise NotImplementedError()


class _MetaDataElement(_Element):
    """
    Base class for metadata elements.
    """
    # TODO: Support multiline metadata (using indentation for the continuation
    #       lines)
    METADATA = None

    def __init__(self, langmark, parent):
        try:
            line = langmark.stream.read_next_lines_buffered(1)[0]
        except StopIteration:
            # Re-raise the exception, but keep this to keep track of where it
            #  comes from
            # Don't just process it here because the element doesn't have to be
            #  instantiated
            raise _EndOfFile()
        else:
            _Element.__init__(self, langmark, parent)
            self.process_match(self.METADATA.fullmatch(line))

    def process_match(self, match):
        raise NotImplementedError()


class HeaderElement(_MetaDataElement):
    """
    A generic key/value metadata element::

        ::key value

    Spaces between ``::`` and the key are ignored.
    The key cannot contain spaces.
    A value string is optional and is considered to start after the first
    sequence of spaces after the key string.
    """
    METADATA = re.compile(r'^\:\:[ \t]*(.+?)(?:[ \t]+(.+?))?[ \t]*\n')

    def process_match(self, match):
        if match:
            self.langmark.header.keys[match.group(1)] = match.group(2)
        else:
            # This is changing the size of INSTALLED_BLOCK_ELEMENTS, so I can't
            #  raise _BlockElementStartNotMatched after it, because that would
            #  simply continue the for loop in
            #  _BlockElement.find_element_start, which would hence skip the
            #  next element in the list
            # Installing this class at the top of INSTALLED_BLOCK_ELEMENTS
            #  makes this as efficient as continuing the loop, since no other
            #  elements are uselessly tested
            _BlockElement.INSTALLED_BLOCK_ELEMENTS.remove(self.__class__)
            self._rewind_check_lines_buffer()
        raise _BlockElementStartConsumed()


class _BlockElement(_Element):
    """
    Base class for block elements.
    """
    INSTALLED_BLOCK_ELEMENTS = None
    TEST_START_LINES = None
    TEST_END_LINES = None
    HTML_BREAK = '\n'
    HTML_TAGS = ('<div>', '</div>')

    def __init__(self, langmark, parent):
        try:
            lines = langmark.stream.read_next_lines_buffered(
                                                        self.TEST_START_LINES)
        except StopIteration:
            # Re-raise the exception, but keep this to keep track of where it
            #  comes from
            # Don't just process it here because the element doesn't have to be
            #  instantiated
            raise _EndOfFile()
        else:
            _Element.__init__(self, langmark, parent)
            self.indentation_external, self.indentation_internal, \
                                initial_lines = self._parse_indentation(lines)
            self._parse_initial_lines(initial_lines)

    def _compute_equivalent_indentation(self, line):
        # TODO: Move to external library
        split = line.split('\t')
        indent = 0
        for chunk in split[:-1]:
            indent += len(chunk) // Configuration.TAB_LENGTH + 1
        indent *= Configuration.TAB_LENGTH
        indent += len(split[-1])
        return indent

    def find_element_start(self):
        while True:
            try:
                for Element in self.INSTALLED_BLOCK_ELEMENTS:
                    try:
                        return Element(self.langmark, self)
                    except (_BlockElementStartNotMatched, _EndOfFile):
                        self._rewind_check_lines_buffer()
                        continue
                return False
            except _BlockElementStartConsumed:
                # Restart the for loop from the beginning
                continue
            else:
                return False

    def _parse_indentation(self, lines):
        raise NotImplementedError()

    def _parse_initial_lines(self, lines):
        raise NotImplementedError()

    def parse_next_line(self):
        raise NotImplementedError()


class _BlockElementContainingBlock(_BlockElement):
    """
    Base class for elements containing block elements.
    """
    def _parse_initial_lines(self, lines):
        self.rewind_lines(*lines)

    def parse_next_line(self):
        element = self.find_element_start()
        if not element:
            try:
                # find_element_start must return False also when the text
                #  would be a Paragraph, so paragraphs (the catch-all elements)
                #  must be created here
                element = Paragraph(self.langmark, self)
            except _BlockElementStartNotMatched:
                # Just discard the consumed lines if really nothing wants them
                self.parse_next_line()
                return
        self._parse_element(element)

    def _parse_element(self, element):
        if element.indentation_external < self.indentation_internal:
            self.parent._parse_element(element)
        else:
            self._add_child(element)
            try:
                element.parse_next_line()
            except _BlockElementStartMatched as exc:
                self._parse_element(exc.element)
                return
            except _BlockElementEndConsumed:
                self.parse_next_line()
                return
            except _BlockElementEndNotConsumed as exc:
                self.rewind_lines(*exc.lines)
                self.parse_next_line()
                return

    def _add_child(self, element):
        element.reset_parent(self)
        # _BlockElementContainingBlock_Prefix_Grouped relies on set_parent to
        #  be called *before* appending the element
        self.children.append(element)

    def convert_to_html(self):
        if len(self.children) > 1:
            # TODO: Re-add the indentation before the tags
            return self.HTML_BREAK.join((self.HTML_TAGS[0],
                            self.HTML_BREAK.join(child.convert_to_html()
                            for child in self.children), self.HTML_TAGS[1]))
        else:
            return self.children[0].convert_to_html().join(self.HTML_TAGS)


class Root(_BlockElementContainingBlock):
    """
    The root element of the tree.

    The first section can start immediately after the header, or be separated
    by no more than one empty line.
    """
    TEST_START_LINES = 1

    def parse_tree(self):
        try:
            self.parse_next_line()
        except _EndOfFile:
            pass

    def _parse_indentation(self, lines):
        return (0, 0, lines)

    def convert_to_html(self):
        return self.HTML_BREAK.join(child.convert_to_html()
                                    for child in self.children)


class _BlockElementContainingBlock_Prefix(_BlockElementContainingBlock):
    """
    Base class for block elements identified by a prefix.

    START_MARK's first capturing group will be used as the first line of
    content.`
    """
    TEST_START_LINES = 1
    BLOCK_MARK = None

    def _parse_indentation(self, lines):
        match = self.BLOCK_MARK.prefix.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        external_indentation = self._compute_equivalent_indentation(
                                                                match.group(1))
        internal_indentation = external_indentation + \
                        self._compute_equivalent_indentation(match.group(2))
        # Remove the prefix, otherwise the same block will be parsed
        #  recursively endlessly
        adapted_line = ''.join((' ' * internal_indentation, match.group(3)))
        return (external_indentation, internal_indentation, (adapted_line, ))


class _BlockElementContainingBlock_Prefix_Grouped(
                                        _BlockElementContainingBlock_Prefix):
    """
    Base class for block elements identified by a prefix that must be grouped
    inside an additional HTML element.
    """
    # TODO: This class should be made a mixin, but it's hard because of the
    #       super calls
    HTML_OUTER_TAGS = None

    def __init__(self, langmark, parent):
        _BlockElementContainingBlock_Prefix.__init__(self, langmark, parent)
        self.group_item_number = 0
        self.group_item_last = True

    def reset_parent(self, element):
        super(_BlockElementContainingBlock_Prefix_Grouped, self).reset_parent(
                                                                    element)
        try:
            previous = element.children[-1]
        except IndexError:
            # The list could be the first element of the document
            pass
        else:
            if previous.__class__ == self.__class__:
                self.group_item_number = previous.group_item_number + 1
                previous.group_item_last = False

    def convert_to_html(self):
        html = super(_BlockElementContainingBlock_Prefix_Grouped,
                     self).convert_to_html()
        if self.group_item_number == 0:
            html = self.HTML_BREAK.join((self.HTML_OUTER_TAGS[0], html))
        if self.group_item_last is True:
            html = self.HTML_BREAK.join((html, self.HTML_OUTER_TAGS[1]))
        return html


class _BlockElementNotContainingBlock_LineMarksMixin:
    """
    A block element, containing inline elements, that starts and ends with
    full-line marks.
    """
    TEST_START_LINES = 1
    TEST_END_LINES = 1
    BLOCK_MARK = None

    def check_element_start(self, lines):
        match = self.BLOCK_MARK.start.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        self.end_mark = self.BLOCK_MARK.make_end_mark(match)
        return (match.group(1), ())

    def _parse_initial_lines(self, lines):
        pass

    def check_element_end(self, lines):
        if self.end_mark.fullmatch(lines[0]):
            raise _BlockElementEndConsumed()


class _BlockElementNotContainingBlock(_BlockElement):
    """
    Base class for elements not containing block elements.
    """
    def __init__(self, langmark, parent):
        self.rawtext = RawText('')
        self.indentation_content = None
        _BlockElement.__init__(self, langmark, parent)

    def _parse_indentation(self, lines):
        indentationtext, initial_lines = self.check_element_start(lines)
        indentation = self._compute_equivalent_indentation(indentationtext)
        return (indentation, indentation, initial_lines)

    def _add_raw_first_line(self, line):
        self.rawtext.append(line[self.indentation_external:])

    def _read_indented_test_end_lines(self, ignore_blank_lines):
        try:
            lines = self.langmark.stream.read_next_lines_buffered(
                                                        self.TEST_END_LINES)
        except StopIteration:
            lines = self.langmark.stream.lines_buffer
            indented_lines = self._check_and_strip_indentation(lines,
                                                            ignore_blank_lines)
            self._add_raw_content_lines(indented_lines)
            self._parse_inline()
            raise _EndOfFile()
        else:
            return self._check_and_strip_indentation(lines, ignore_blank_lines)

    def _check_and_strip_indentation(self, lines, ignore_blank_lines):
        indented_lines = []
        for lN, line in enumerate(lines):
            if Configuration.BLANK_LINE.fullmatch(line):
                if not ignore_blank_lines:
                    self._parse_inline()
                    raise _BlockElementEndNotConsumed(*lines[lN:])
                # Never strip the line break from blank lines
                # If self.indentation_content hasn't been set yet, it behaves
                #  like 0 in string slicing
                indented_lines.append(line[self.indentation_content:-1] +
                                      line[-1])
            else:
                indentation = self._compute_equivalent_indentation(
                                Configuration.INDENTATION.match(line).group())
                try:
                    if indentation < self.indentation_content:
                        self._parse_inline()
                        raise _BlockElementEndNotConsumed(*lines[lN:])
                except TypeError:
                    self.indentation_content = min(indentation,
                                                   self.indentation_external)
                indented_lines.append(line[self.indentation_content:])
        return indented_lines

    def _add_raw_content_lines(self, lines):
        self.rawtext.append(''.join(lines))

    def check_element_start(self, lines):
        raise NotImplementedError()

    def check_element_end(self, lines):
        raise NotImplementedError()

    def _parse_inline(self):
        raise NotImplementedError()


class _BlockElementContainingInline_Meta(_BlockElementNotContainingBlock):
    """
    Meta class for elements containing inline elements.
    """
    def _parse_inline(self):
        inline_parser = textparser.TextParser(self.rawtext.text)
        dummyelement = BaseInlineElement(self.langmark, self, inline_parser,
                                         None, None, None)
        dummyelement.take_inline_control()
        inline_parser.parse()
        self.children = dummyelement.children


class Paragraph(_BlockElementContainingInline_Meta):
    """
    A paragraph.

    The default container, it ends whenever an empty line is found. If multiple
    empty lines are found, all except the last one are considered part of the
    content.
    """
    TEST_START_LINES = 1
    TEST_END_LINES = 1
    HTML_TAGS = ('<p>', '</p>')

    def check_element_start(self, lines):
        line = lines[0]
        if Configuration.BLANK_LINE.fullmatch(line):
            raise _BlockElementStartNotMatched()
        indentation = Configuration.INDENTATION.match(line).group()
        return (indentation, lines)

    def _parse_initial_lines(self, lines):
        self._add_raw_first_line(lines[0])

    def parse_next_line(self):
        element = self.find_element_start()
        if element:
            self._parse_inline()
            raise _BlockElementStartMatched(element)
        lines = self._read_indented_test_end_lines(ignore_blank_lines=False)
        self._add_raw_content_lines(lines)
        self.parse_next_line()

    # If an inline mark has overlapping matches with an inline mark, **which
    #  should never happen by design**, it's impossible to only escape the
    #  block mark leaving the inline mark intact; if an escape character is
    #  added at the beginning of a line, it will always escape both.
    #  In theory the following overriding method would allow escaping the block
    #  mark with 1 escape character, escaping the inline mark with 2, and
    #  starting a line with an escaped escape character with 3, but all this
    #  would not feel natural. As said above, all marks, both block and inline,
    #  should be designed to never overlap.
    # Also note that the original method has changed since this override was
    #  implemented.
    #def _add_raw_line(self, line):
    #    if Configuration.ESCAPE_RE.match(line):
    #        line = line[1:]
    #    super(Paragraph, self)._add_raw_line(line)

    def convert_to_html(self):
        html = self._trim_last_break(''.join(child.convert_to_html()
                                             for child in self.children))
        if len(self.parent.children) > 1:
            return html.join(self.HTML_TAGS)
        else:
            return html


class _BlockElementContainingInline(_BlockElementContainingInline_Meta):
    """
    Base class for elements containing inline elements.
    """
    def parse_next_line(self):
        lines = self._read_indented_test_end_lines(ignore_blank_lines=True)
        try:
            self.check_element_end(lines)
        except (_BlockElementStartMatched, _BlockElementEndConsumed,
                _BlockElementEndNotConsumed):
            self._parse_inline()
            raise
        else:
            self._add_raw_content_lines(lines)
            self.parse_next_line()

    def convert_to_html(self):
        html = self._trim_last_break(''.join(
                        child.convert_to_html() for child in self.children))
        return html.join(self.HTML_TAGS)


class _BlockElementContainingInline_LineMarks(
                                _BlockElementNotContainingBlock_LineMarksMixin,
                                _BlockElementContainingInline):
    """
    A block element, containing inline elements, that starts and ends with
    full-line marks.
    """
    pass


class _BlockElementNotContainingInline(_BlockElementNotContainingBlock):
    """
    Base class for elements containing neither inline nor block elements.
    """
    def parse_next_line(self):
        lines = self._read_indented_test_end_lines(ignore_blank_lines=True)
        self.check_element_end(lines)
        self._add_raw_content_lines(lines)
        self.parse_next_line()

    def _parse_inline(self):
        pass


class _BlockElementContainingRaw_LineMarks(
                                _BlockElementNotContainingBlock_LineMarksMixin,
                                _BlockElementNotContainingInline):
    """
    A block element, containing raw text, that starts and ends with full-line
    marks.
    """
    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.get_raw_text()).join(
                                                                self.HTML_TAGS)


class _BlockElementContainingText_LineMarks(
                                _BlockElementNotContainingBlock_LineMarksMixin,
                                _BlockElementNotContainingInline):
    """
    A block element, containing plain text, that starts and ends with full-line
    marks.
    """
    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.convert_to_html()).join(
                                                                self.HTML_TAGS)


class _InlineElement(_Element):
    """
    Base class for inline elements.
    """
    ENABLE_ESCAPE = None
    START_MARK_TO_INLINE_ELEMENT = None
    INLINE_MARK = None
    HTML_TAGS = ('<span>', '</span>')

    def __init__(self, langmark, parent, inline_parser, parsed_text,
                 start_mark, is_element_start):
        self.inline_parser = inline_parser
        self.inline_bindings = self.install_bindings(parsed_text, start_mark,
                                                            is_element_start)
        if self.ENABLE_ESCAPE:
            self.inline_bindings[Configuration.ESCAPE_RE] = \
                                                    self._handle_inline_escape
        _Element.__init__(self, langmark, parent)

    def install_bindings(self, parsed_text, start_mark, is_element_start):
        raise NotImplementedError()

    def take_inline_control(self):
        self.inline_parser.reset_bindings(self.inline_bindings)
        self.inline_parser.bind_to_parse_end(self._handle_inline_parse_end)

    def _handle_inline_escape(self, event):
        self.children.append(RawText(event.parsed_text +
                                     event.mark.group()[1]))

    def _handle_inline_end_mark(self, event):
        if self.INLINE_MARK.check_end_mark(event.parsed_text, event.mark):
            self._post_process_inline(event.parsed_text)
            self.parent.take_inline_control()
        else:
            self.children.append(RawText(''.join((event.parsed_text,
                                                  event.mark.group()))))

    def _handle_inline_parse_end(self, event):
        self._post_process_inline(event.remainder_text)

    def _post_process_inline(self, text):
        self.children.append(RawText(text))
        try:
            self.post_process_inline()
        except NotImplementedError:
            pass

    def post_process_inline(self):
        raise NotImplementedError()


class _InlineElementContainingInline(_InlineElement):
    """
    Base class for inline elements containing inline elements.
    """
    ENABLE_ESCAPE = True

    def install_bindings(self, parsed_text, start_mark, is_element_start):
        bindings = {start_mark: self._handle_inline_start_mark
                    for start_mark in self.START_MARK_TO_INLINE_ELEMENT}
        # BaseInlineElement passes None as start_mark
        if start_mark:
            end_mark = self.INLINE_MARK.make_end_mark(parsed_text, start_mark,
                                                            is_element_start)
            bindings[end_mark] = self._handle_inline_end_mark
        return bindings

    def _handle_inline_start_mark(self, event):
        try:
            element = self.START_MARK_TO_INLINE_ELEMENT[event.regex](
                        self.langmark, self, self.inline_parser,
                        event.parsed_text, event.mark, not bool(self.children))
        except _InlineElementStartNotMatched:
            self.children.append(RawText(''.join((event.parsed_text,
                                                  event.mark.group()))))
        else:
            self.children.append(RawText(event.parsed_text))
            self.children.append(element)
            element.take_inline_control()

    def convert_to_html(self):
        html = self._trim_last_break(''.join(child.convert_to_html()
                                             for child in self.children))
        return html.join(self.HTML_TAGS)


class BaseInlineElement(_InlineElementContainingInline):
    """
    Dummy inline element for parsing other inline elements.
    """
    INLINE_MARK = None


class _InlineElementContainingParameters(_InlineElement):
    """
    Base class for inline elements containing parameters.
    """
    ENABLE_ESCAPE = True

    def __init__(self, *args, **kwargs):
        self.parameters = []
        _InlineElement.__init__(self, *args, **kwargs)

    def install_bindings(self, parsed_text, start_mark, is_element_start):
        parameter_mark, end_mark = \
                                self.INLINE_MARK.make_parameter_and_end_marks(
                                parsed_text, start_mark, is_element_start)
        return {parameter_mark: self._handle_parameter_mark,
                end_mark: self._handle_inline_end_mark}

    def _handle_parameter_mark(self, event):
        if self.INLINE_MARK.check_parameter_mark(event.parsed_text,
                                                 event.mark):
            self.children.append(RawText(event.parsed_text))
            self._finalize_parameter()
        else:
            self.children.append(RawText(''.join((event.parsed_text,
                                                  event.mark.group()))))

    def _finalize_parameter(self):
        self.parameters.append(_Parameter(self.langmark, self, self.children))
        self.children = []

    def post_process_inline(self):
        self._finalize_parameter()
        self.children = self.parameters
        self.parameters = []
        try:
            self.post_process_parameters()
        except NotImplementedError:
            pass

    def post_process_parameters(self):
        raise NotImplementedError()


class _Parameter(_Element):
    """
    A parameter element.
    """
    def __init__(self, langmark, parent, children):
        _Element.__init__(self, langmark, parent)
        self.children[:] = children

    def get_raw_text(self):
        return ''.join(child.get_raw_text() for child in self.children)

    def convert_to_html(self):
        return ''.join(child.convert_to_html() for child in self.children)


class _InlineElementContainingText(_InlineElement):
    """
    Base class for inline elements containing text.
    """
    def install_bindings(self, parsed_text, start_mark, is_element_start):
        end_mark = self.INLINE_MARK.make_end_mark(parsed_text, start_mark,
                                                  is_element_start)
        return {end_mark: self._handle_inline_end_mark}


class _InlineElementContainingRawText(_InlineElementContainingText):
    """
    Base class for inline elements containing raw text.
    """
    ENABLE_ESCAPE = False

    def convert_to_html(self):
        return ''.join(child.get_raw_text() for child in self.children
                                                        ).join(self.HTML_TAGS)


class _InlineElementContainingHtmlText(_InlineElementContainingText):
    """
    Base class for inline elements containing plain text.
    """
    ENABLE_ESCAPE = False

    def convert_to_html(self):
        return ''.join(child.convert_to_html() for child in self.children
                                                        ).join(self.HTML_TAGS)
