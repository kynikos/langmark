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
import itertools
import textparser




class _Regexs:
    """
    Auxiliary regular expressions and other constants.
    """
    TAB_LENGTH = 4
    BLANK_LINE = re.compile(r'^[ \t]*\n')
    INDENTATION = re.compile(r'^[ \t]*')
    # If an inline mark has overlapping matches with an inline mark, **which
    #  should never happen by design**, it's impossible to only escape the
    #  block mark leaving the inline mark intact; if an escape character is
    #  added at the beginning of a line, it will always escape both.
    ESCAPE_CHAR = re.compile('`.')


class Stream:
    """
    The document stream.
    """
    def __init__(self, stream):
        self.stream = stream

    def read_next_line(self):
        # Do *not* use this method without protecting it from StopIteration
        #   and properly rewinding the parsed lines in case they aren't used!!!
        #  If possible, don't use this method at all (just rely on the core
        #   engine
        return next(self.stream)

    def read_next_lines_buffered(self, N):
        # Do *not* use this method without protecting it from StopIteration
        #   and properly rewinding the parsed lines in case they aren't used!!!
        #  If possible, don't use this method at all (just rely on the core
        #   engine
        self.lines_buffer = []
        # Don't use a list comprehension because StopIteration can be raised
        #  and the buffer must contain the last iterated lines
        for n in range(N):
            self.lines_buffer.append(self.read_next_line())
        return self.lines_buffer

    def rewind_lines(self, *lines):
        self.stream = itertools.chain(lines, self.stream)


class Header:
    """
    The header of the document, hosting the meta data.::

        ::key value
        ::key value
        ::key value

    All the lines must start with ``::``.
    Spaces between ``::`` and the key are ignored.
    The key cannot contain spaces.
    A value string is optional and is considered to start after the first
    sequence of spaces after the key string.
    Multiline values are not supported yet.
    The header ends as soon as a line that does not start with ``::`` is found.
    """
    # TODO: Support multiline metadata (using indentation for the continuation
    #       lines)
    METADATA = re.compile(r'^\:\:[ \t]*(.+?)(?:[ \t]+(.+?))?[ \t]*\n')

    def __init__(self, stream):
        self.stream = stream
        self.keys = {}

    def parse_next_line(self):
        while True:
            line = self.stream.read_next_line()
            match = self.METADATA.fullmatch(line)
            if match:
                self.keys[match.group(1)] = match.group(2)
                self.parse_next_line()
            else:
                # Inserting an emtpy line makes sure that elements starting
                #  with an empty line, like multiline headings, are recognized
                self.stream.rewind_lines('\n', line)
                break


class _InlineMarkFactory:
    """
    Base class for inline mark factories.
    """
    pass


class InlineMarkSimple(_InlineMarkFactory):
    """
    A simple sequence of the same character.
    """
    # Note how marks at the end of lines are ignored
    START_NORMAL = (r'(^{escaped_char}+[ \t]*|{escaped_char}+)'
                     '(?![{escaped_char} \t\n]|$)')
    # Note how marks at the end of lines are ignored
    START_SPACED = r'(?<!^)[ \t]+{escaped_char}+[ \t]+(?!\n|$)'
    END_NORMAL = r'(?<![ \t])'
    END_SPACED = ' '

    def __init__(self, char):
        # Make sure that char is a single character
        escaped_char = re.escape(char[0])
        self.normal = re.compile(self.START_NORMAL.format(
                                                    escaped_char=escaped_char))
        self.spaced = re.compile(self.START_SPACED.format(
                                                    escaped_char=escaped_char))

    @classmethod
    def make_end_mark_normal(cls, start_mark):
        return re.compile(cls.END_NORMAL + re.escape(start_mark))

    @classmethod
    def make_end_text_normal(cls, parsed_text):
        return parsed_text

    @classmethod
    def make_end_mark_spaced(cls, start_mark):
        # Don't match the last space ([:-1]), so that it's added after the
        #  closing HTML tag
        return re.compile(re.escape(start_mark[:-1]))

    @classmethod
    def make_end_text_spaced(cls, parsed_text):
        return parsed_text + cls.END_SPACED


class RawText:
    def __init__(self, text):
        self.text = text

    def append(self, text):
        self.text = ''.join((self.text, text))

    def get_raw_text(self):
        return self.text

    def convert_to_html(self):
        # "&" must be escaped *before* everything else
        text = self.text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        return text


class _BlockElementStartNotMatched(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    does not correspond to the start of the element.
    """
    pass


class _BlockElementStartMatched(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    corresponds to the start of a new element.
    """
    def __init__(self, element):
        self.element = element


class _EndOfFile(Exception):
    """
    Internal exception used to communicate to the parent that the creation of
    an element has been stopped by the end of file.
    """
    pass


class _BlockElementEndConsumed(Exception):
    """
    Internal exception used to communicate the end of the element to its
    parent. The parsed line has been consumed.
    """
    pass


class _BlockElementEndNotConsumed(Exception):
    """
    Internal exception used to communicate the end of the element to its
    parent. The parsed line must be consumed by the parent.
    """
    def __init__(self, *lines):
        self.lines = lines


class _Element:
    """
    Base class for document elements.
    """
    def __init__(self):
        self.parent = None
        self.children = []

    def set_parent(self, element):
        self.parent = element

    @staticmethod
    def _trim_last_break(text):
        if text.endswith('\n'):
            return text[:-1]
        return text

    def convert_to_html(self):
        # TODO: Convert to HTML *while* building the tree, not afterwards
        #       (use events?)
        raise NotImplementedError()


class _BlockElement(_Element):
    """
    Base class for block elements.
    """
    STREAM = None
    INSTALLED_BLOCK_ELEMENTS = None
    TEST_START_LINES = None
    TEST_END_LINES = None
    HTML_BREAK = '\n'
    HTML_TAGS = ('<div>', '</div>')

    def __init__(self):
        try:
            lines = self._read_start_check_lines()
        except StopIteration:
            # Re-raise the exception, but keep this to keep track of where it
            #  comes from
            # Don't just process it here because the element doesn't have to be
            #  instantiated
            raise _EndOfFile()
        else:
            _Element.__init__(self)
            indentation_external, indentation_internal, initial_lines = \
                                                self._parse_indentation(lines)
            self.indentation_external = self._compute_equivalent_indentation(
                                                        indentation_external)
            self.indentation_internal = self.indentation_external + \
                    self._compute_equivalent_indentation(indentation_internal)
            self._parse_initial_lines(initial_lines)

    def _compute_equivalent_indentation(self, line):
        # TODO: Move to external library
        split = line.split('\t')
        indent = 0
        for chunk in split[:-1]:
            indent += len(chunk) // _Regexs.TAB_LENGTH + 1
        indent *= _Regexs.TAB_LENGTH
        indent += len(split[-1])
        return indent

    def _parse_indentation(self, lines):
        raise NotImplementedError()

    def _parse_initial_lines(self, lines):
        raise NotImplementedError()

    def parse_next_line(self):
        raise NotImplementedError()

    def find_element_start(self):
        for Element in self.INSTALLED_BLOCK_ELEMENTS:
            try:
                return Element()
            except (_BlockElementStartNotMatched, _EndOfFile):
                self._rewind_check_lines_buffer()
                continue
        return False

    def _read_start_check_lines(self):
        # Do *not* use this method without protecting it from StopIteration
        #   and properly rewinding the parsed lines in case they aren't used!!!
        #  If possible, don't use this method at all (just rely on the core
        #   engine
        return _BlockElement.STREAM.read_next_lines_buffered(
                                                        self.TEST_START_LINES)

    def _read_end_check_lines(self):
        # Do *not* use this method without protecting it from StopIteration
        #   and properly rewinding the parsed lines in case they aren't used!!!
        #  If possible, don't use this method at all (just rely on the core
        #   engine
        return _BlockElement.STREAM.read_next_lines_buffered(
                                                        self.TEST_END_LINES)

    def _read_check_lines_buffer(self):
        return _BlockElement.STREAM.lines_buffer

    def _rewind_check_lines_buffer(self):
        self.rewind_lines(*self._read_check_lines_buffer())

    def rewind_lines(self, *lines):
        _BlockElement.STREAM.rewind_lines(*lines)


class _InlineElement(_Element):
    """
    Base class for inline elements.
    """
    START_MARK_NORMAL_TO_INLINE_ELEMENT = None
    START_MARK_SPACED_TO_INLINE_ELEMENT = None
    ENABLE_ESCAPE = True
    HTML_TAGS = ('<span>', '</span>')

    def __init__(self, parent, inline_parser, end_mark):
        self.inline_parser = inline_parser
        self.inline_bindings = {
            start_mark_normal: self._handle_inline_start_mark_normal
            for start_mark_normal in self.START_MARK_NORMAL_TO_INLINE_ELEMENT}
        self.inline_bindings.update(
            {start_mark_spaced: self._handle_inline_start_mark_spaced
            for start_mark_spaced in self.START_MARK_SPACED_TO_INLINE_ELEMENT})
        # BaseInlineElement passes None as end_mark
        if end_mark:
            self.inline_bindings[end_mark] = self._handle_inline_end_mark
        if self.ENABLE_ESCAPE:
            self.inline_bindings[_Regexs.ESCAPE_CHAR] = \
                                                    self._handle_inline_escape
        _Element.__init__(self)
        self.set_parent(parent)

    @classmethod
    def install_marks(cls, start_mark_normal_to_element, start_mark_normal,
                      start_mark_spaced_to_element, start_mark_spaced):
        raise NotImplementedError()

    def take_inline_control(self):
        self.inline_parser.reset_bindings(self.inline_bindings)
        self.inline_parser.bind_to_parse_end(self._handle_inline_parse_end)

    def _handle_inline_escape(self, event):
        self.children.append(RawText(event.parsed_text +
                                     event.mark.group()[1]))

    def _handle_inline_start_mark_normal(self, event):
        end_mark = InlineMarkSimple.make_end_mark_normal(event.mark.group())
        element = self.START_MARK_NORMAL_TO_INLINE_ELEMENT[event.regex](self,
                                                self.inline_parser, end_mark)
        self._append_element(InlineMarkSimple.make_end_text_normal(
                                                event.parsed_text), element)

    def _handle_inline_start_mark_spaced(self, event):
        end_mark = InlineMarkSimple.make_end_mark_spaced(event.mark.group())
        element = self.START_MARK_SPACED_TO_INLINE_ELEMENT[event.regex](self,
                                                self.inline_parser, end_mark)
        self._append_element(InlineMarkSimple.make_end_text_spaced(
                                                event.parsed_text), element)

    def _append_element(self, parsed_text, element):
        self.children.append(RawText(parsed_text))
        self.children.append(element)
        element.take_inline_control()

    def _handle_inline_end_mark(self, event):
        self.children.append(RawText(event.parsed_text))
        self.parent.take_inline_control()

    def _handle_inline_parse_end(self, event):
        self.children.append(RawText(event.remainder_text))


class _BlockElementContainingBlock(_BlockElement):
    """
    Base class for elements containing block elements.
    """
    def _parse_initial_lines(self, lines):
        self.rewind_lines(*self._adapt_initial_lines(lines))

    def _adapt_initial_lines(self, lines):
        raise NotImplementedError()

    def parse_next_line(self):
        element = self.find_element_start()
        if not element:
            try:
                # find_element_start must return False also when the text
                #  would be a Paragraph, so paragraphs (the catch-all elements)
                #  must be created here
                element = Paragraph()
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
        element.set_parent(self)
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


class _BlockElementNotContainingBlock(_BlockElement):
    """
    Base class for elements not containing block elements.
    """
    def __init__(self):
        self.rawtext = RawText('')
        self.indentation_content = None
        _BlockElement.__init__(self)

    def _parse_indentation(self, lines):
        indentation, initial_lines = self.check_element_start(lines)
        return (indentation, '', initial_lines)

    def check_element_start(self, lines):
        raise NotImplementedError()

    def check_element_end(self, lines):
        raise NotImplementedError()

    def _add_raw_first_line(self, line):
        self.rawtext.append(line[self.indentation_external:])

    def _check_indentation_and_add_raw_lines(self, lines):
        for lN, line in enumerate(lines):
            indentation = self._compute_equivalent_indentation(
                                    _Regexs.INDENTATION.match(line).group())
            try:
                if indentation < self.indentation_content:
                    self._parse_inline()
                    raise _BlockElementEndNotConsumed(*lines[lN:])
            except TypeError:
                self.indentation_content = indentation
            self.rawtext.append(line[self.indentation_content:])

    def _parse_inline(self):
        inline_parser = textparser.TextParser(self.rawtext.text)
        dummyelement = BaseInlineElement(self, inline_parser, None)
        dummyelement.take_inline_control()
        inline_parser.parse()
        self.children = dummyelement.children


class _BlockElementContainingInline(_BlockElementNotContainingBlock):
    """
    Base class for elements containing inline elements.
    """
    def parse_next_line(self):
        try:
            lines = self._read_end_check_lines()
        except StopIteration:
            lines = self._read_check_lines_buffer()
            self._check_indentation_and_add_raw_lines(lines)
            self._parse_inline()
            raise _EndOfFile()
        else:
            try:
                self.check_element_end(lines)
            except (_BlockElementStartMatched, _BlockElementEndConsumed,
                    _BlockElementEndNotConsumed):
                self._parse_inline()
                raise
            else:
                self._check_indentation_and_add_raw_lines(lines)
                self.parse_next_line()

    def convert_to_html(self):
        html = self._trim_last_break(''.join(
                        child.convert_to_html() for child in self.children))
        return html.join(self.HTML_TAGS)


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
        return ('', '', lines)

    def _adapt_initial_lines(self, lines):
        return lines

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
    START_MARK = None

    def _parse_indentation(self, lines):
        match = self.START_MARK.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        return (match.group(1), match.group(2), (match.group(3), ))

    def _adapt_initial_lines(self, lines):
        # Remove the prefix, otherwise the same block will be parsed
        #  recursively endlessly
        return (''.join((' ' * self.indentation_internal, lines[0])), )


class _BlockElementContainingBlock_Prefix_Grouped(
                                        _BlockElementContainingBlock_Prefix):
    """
    Base class for block elements identified by a prefix that must be grouped
    inside an additional HTML element.
    """
    # TODO: This class should be made a mixin, but it's hard because of the
    #       super calls
    HTML_OUTER_TAGS = None

    def __init__(self):
        super(_BlockElementContainingBlock_Prefix_Grouped, self).__init__()
        self.group_item_number = 0
        self.group_item_last = True

    def set_parent(self, element):
        super(_BlockElementContainingBlock_Prefix_Grouped, self).set_parent(
                                                                    element)
        previous = element.children[-1]
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


class _BlockElementContainingInline_LineMarks(_BlockElementContainingInline):
    """
    A block element, containing inline elements, that starts and ends with
    full-line marks.
    """
    TEST_START_LINES = 1
    TEST_END_LINES = 1
    START_MARK = None
    END_MARK = None

    def check_element_start(self, lines):
        match = self.START_MARK.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        return (match.group(1), ())

    def _parse_initial_lines(self, lines):
        pass

    def check_element_end(self, lines):
        match = self.END_MARK.fullmatch(lines[0])
        if match:
            raise _BlockElementEndConsumed()


class Paragraph(_BlockElementNotContainingBlock):
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
        if _Regexs.BLANK_LINE.fullmatch(line):
            raise _BlockElementStartNotMatched()
        indentation = _Regexs.INDENTATION.match(line).group()
        return (indentation, lines)

    def _parse_initial_lines(self, lines):
        self._add_raw_first_line(lines[0])

    def parse_next_line(self):
        element = self.find_element_start()
        if element:
            self._parse_inline()
            raise _BlockElementStartMatched(element)
        try:
            lines = self._read_end_check_lines()
        except StopIteration:
            lines = self._read_check_lines_buffer()
            self._check_indentation_and_add_raw_lines(lines)
            self._parse_inline()
            raise _EndOfFile()
        else:
            if _Regexs.BLANK_LINE.fullmatch(lines[0]):
                self._parse_inline()
                raise _BlockElementEndConsumed()
            self._check_indentation_and_add_raw_lines(lines)
            self.parse_next_line()
            return

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
    #    if _Regexs.ESCAPE_CHAR.match(line):
    #        line = line[1:]
    #    super(Paragraph, self)._add_raw_line(line)

    def convert_to_html(self):
        html = self._trim_last_break(''.join(child.convert_to_html()
                                             for child in self.children))
        if len(self.parent.children) > 1:
            return html.join(self.HTML_TAGS)
        else:
            return html


class _BlockElementNotContainingInline_LineMarks(
                                            _BlockElementNotContainingBlock):
    """
    Base class for elements containing neither inline nor block elements, that
    starts and ends with full-line marks.
    """
    TEST_START_LINES = 1
    TEST_END_LINES = 1
    START_MARK = None
    END_MARK = None

    def check_element_start(self, lines):
        match = self.START_MARK.fullmatch(lines[0])
        if not match:
            raise _BlockElementStartNotMatched()
        return (match.group(1), ())

    def _parse_initial_lines(self, lines):
        pass

    def parse_next_line(self):
        try:
            lines = self._read_end_check_lines()
        except StopIteration:
            # It would be safe to just pass here because self.TEST_END_LINES
            #  is 1, however just make it safe to adapt to possible future
            #  changes
            lines = self._read_check_lines_buffer()
            self._check_indentation_and_add_raw_lines(lines)
            raise _EndOfFile()
        else:
            self.check_element_end(lines)
            self._check_indentation_and_add_raw_lines(lines)
            self.parse_next_line()

    def check_element_end(self, lines):
        match = self.END_MARK.fullmatch(lines[0])
        if match:
            raise _BlockElementEndConsumed()


class _BlockElementContainingText_LineMarks(
                                _BlockElementNotContainingInline_LineMarks):
    """
    A block element, containing plain text, that starts and ends with full-line
    marks.
    """
    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.convert_to_html()).join(
                                                                self.HTML_TAGS)


class _BlockElementContainingRaw_LineMarks(
                                _BlockElementNotContainingInline_LineMarks):
    """
    A block element, containing raw text, that starts and ends with full-line
    marks.
    """
    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.get_raw_text()).join(
                                                                self.HTML_TAGS)


class _InlineElementContainingInline(_InlineElement):
    """
    Base class for inline elements containing inline elements.
    """
    INLINE_MARK = None

    @classmethod
    def install_marks(cls, start_mark_normal_to_element, start_mark_normal,
                      start_mark_spaced_to_element, start_mark_spaced):
        del start_mark_normal_to_element[start_mark_normal]
        del start_mark_spaced_to_element[start_mark_spaced]
        cls.START_MARK_NORMAL_TO_INLINE_ELEMENT = start_mark_normal_to_element
        cls.START_MARK_SPACED_TO_INLINE_ELEMENT = start_mark_spaced_to_element
        cls.ENABLE_ESCAPE = True

    def convert_to_html(self):
        html = self._trim_last_break(''.join(child.convert_to_html()
                                             for child in self.children))
        return html.join(self.HTML_TAGS)


class _InlineElementNotContainingInline(_InlineElement):
    """
    Base class for inline elements not containing inline elements.
    """
    @classmethod
    def install_marks(cls, start_mark_normal_to_element, start_mark_normal,
                      start_mark_spaced_to_element, start_mark_spaced):
        cls.START_MARK_NORMAL_TO_INLINE_ELEMENT = {}
        cls.START_MARK_SPACED_TO_INLINE_ELEMENT = {}
        cls.ENABLE_ESCAPE = False


class _InlineElementContainingText(_InlineElementNotContainingInline):
    """
    Base class for inline elements containing plain text.
    """
    INLINE_MARK = None

    def convert_to_html(self):
        return ''.join(child.convert_to_html() for child in self.children
                                                        ).join(self.HTML_TAGS)


class _InlineElementContainingRaw(_InlineElementNotContainingInline):
    """
    Base class for inline elements containing raw text.
    """
    INLINE_MARK = None

    def convert_to_html(self):
        return ''.join(child.get_raw_text() for child in self.children
                                                        ).join(self.HTML_TAGS)


class BaseInlineElement(_InlineElement):
    """
    Dummy inline element for parsing other inline elements.
    """
    @classmethod
    def install_marks(cls, start_mark_normal_to_element, start_mark_normal,
                      start_mark_spaced_to_element, start_mark_spaced):
        cls.START_MARK_NORMAL_TO_INLINE_ELEMENT = start_mark_normal_to_element
        cls.START_MARK_SPACED_TO_INLINE_ELEMENT = start_mark_spaced_to_element
        cls.ENABLE_ESCAPE = True
