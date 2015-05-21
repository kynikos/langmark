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




class Marks:
    """
    The regular expressions used to detect start and end of elements.
    """
    METADATA = re.compile(r'^\:\:[ \t]*(.+?)(?:[ \t]+(.+?))?[ \t]*\n')
    BLANK_LINE = re.compile(r'^[ \t]*\n')
    PARAGRAPH_INDENTATION = re.compile(r'^[ \t]*')
    BLOCK_ESCAPE = '`'


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
    def __init__(self):
        self.keys = {}

    def parse(self, stream):
        for line in stream:
            match = Marks.METADATA.fullmatch(line)
            if match:
                self.keys[match.group(1)] = match.group(2)
            else:
                return line
        # Never return None
        return ''


class RawText:
    def __init__(self, text):
        self.text = text

    def __bool__(self):
        return len(self.text) > 0

    def append(self, text):
        self.text = ''.join((self.text, text))

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
    def __init__(self, line):
        self.line = line


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
    HTML_BREAK = '\n'
    HTML_TAGS = ('<div>', '</div>')

    def __init__(self, line):
        self.indentation_external, self.indentation_internal, indented_line = \
                                                    self.parse_first_line(line)
        _Element.__init__(self)
        # The first line might need to be ignored
        if indented_line is not None:
            self.STREAM = itertools.chain(
                (''.join((' ' * self.indentation_internal, indented_line)), ),
                self.STREAM)

    def find_element_start(self, line):
        for Element in self.INSTALLED_BLOCK_ELEMENTS:
            try:
                return Element(line)
            except _BlockElementStartNotMatched:
                continue
        return False

    def parse_lines(self):
        for line in self.STREAM:
            self.parse_line(line)
        # This allows recognizing the last paragraph
        self.parse_line("\n")

    def parse_first_line(self, line):
        raise NotImplementedError()

    def parse_line(self, line):
        raise NotImplementedError()


class _InlineElement(_Element):
    """
    Base class for inline elements.
    """
    START_MARK_TO_INLINE_ELEMENT = None
    END_MARK = None
    HTML_TAGS = ('<span>', '</span>')

    def __init__(self, inline_parser):
        self.inline_parser = inline_parser
        self.inline_bindings = {start_mark: self._handle_inline_start_mark
                        for start_mark in self.START_MARK_TO_INLINE_ELEMENT}
        if self.END_MARK:
            self.inline_bindings[self.END_MARK] = self._handle_inline_end_mark
        _Element.__init__(self)

    @classmethod
    def install_marks(cls, start_mark_to_element, start_mark, end_mark):
        raise NotImplementedError()

    def take_inline_control(self):
        self.inline_parser.reset_bindings(self.inline_bindings)
        self.inline_parser.bind_to_parse_end(self._handle_inline_parse_end)

    def _handle_inline_start_mark(self, event):
        self.children.append(RawText(event.parsed_text))
        element = self.START_MARK_TO_INLINE_ELEMENT[event.regex](
                                                            self.inline_parser)
        self.children.append(element)
        element.set_parent(self)
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
    def parse_line(self, line):
        element = self.find_element_start(line)
        if not element:
            try:
                # find_element_start must return False also when the text
                #  would be a Paragraph, so paragraphs (the catch-all elements)
                #  must be created here
                element = Paragraph(line)
            except _BlockElementStartNotMatched:
                return
        self._parse_element(element)

    def _parse_element(self, element):
        if element.indentation_external < self.indentation_internal:
            self.parent._parse_element(element)
        else:
            self._add_child(element)
            try:
                element.parse_lines()
            except _BlockElementStartMatched as exc:
                self._parse_element(exc.element)
                return
            except _BlockElementEndConsumed:
                return
            except _BlockElementEndNotConsumed as exc:
                self.parse_line(exc.line)
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
    def __init__(self, line):
        self.rawtext = RawText('')
        _BlockElement.__init__(self, line)

    def _add_raw_line(self, line):
        self.rawtext.append(line[self.indentation_external:])

    def check_last_line(self, line):
        raise NotImplementedError()


class _BlockElementContainingInline(_BlockElementNotContainingBlock):
    """
    Base class for elements containing inline elements.
    """
    def parse_line(self, line):
        try:
            self.check_last_line(line)
        except (_BlockElementStartMatched, _BlockElementEndConsumed,
                _BlockElementEndNotConsumed):
            inline_parser = textparser.TextParser(self.rawtext.text)
            dummyelement = DummyInlineElement(inline_parser)
            dummyelement.take_inline_control()
            inline_parser.parse()
            self.children = dummyelement.children
            raise
        else:
            self._add_raw_line(line)

    def convert_to_html(self):
        html = self._trim_last_break(''.join(
                        child.convert_to_html() for child in self.children))
        return html.join(self.HTML_TAGS)


class _BlockElementContainingText(_BlockElementNotContainingBlock):
    """
    Base class for elements containing plain text.
    """
    def parse_line(self, line):
        self.check_last_line(line)
        self._add_raw_line(line)

    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.convert_to_html()).join(
                                                                self.HTML_TAGS)


class Root(_BlockElementContainingBlock):
    """
    The root element of the tree.

    The first section can start immediately after the header, or be separated
    by no more than one empty line.
    """
    HTML_TAGS = ('', '')

    def parse_first_line(self, line):
        return (0, 0, line)

    def convert_to_html(self):
        return self.HTML_BREAK.join(child.convert_to_html()
                                    for child in self.children)


class _BlockElementContainingBlock_Prefix(_BlockElementContainingBlock):
    """
    Base class for block elements identified by a prefix.

    START_MARK's first capturing group will be used as the first line of
    content.`
    """
    START_MARK = None

    def parse_first_line(self, line):
        match = self.START_MARK.fullmatch(line)
        if not match:
            raise _BlockElementStartNotMatched()
        return (len(match.group(2)), len(match.group(1)), match.group(3))


class _BlockElementContainingBlock_Prefix_Grouped(
                                        _BlockElementContainingBlock_Prefix):
    """
    Base class for block elements identified by a prefix that must be grouped
    inside an additional HTML element.
    """
    # TODO: This class should be made a mixin, but it's hard because of the
    #       super calls
    HTML_OUTER_TAGS = None

    def __init__(self, line):
        super(_BlockElementContainingBlock_Prefix_Grouped, self).__init__(line)
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


class _BlockElementContainingInline_OneLine(_BlockElementContainingInline):
    """
    A block element, containing inline elements, that can only span one line
    and is identified by a prefix.

    START_MARK's first capturing group will be used as the element content.
    """
    START_MARK = None

    def parse_first_line(self, line):
        match = self.START_MARK.match(line)
        if not match:
            raise _BlockElementStartNotMatched()
        indent = len(match.group(1))
        return (indent, indent, match.group(2))

    def check_last_line(self, line):
        if self.rawtext:
            raise _BlockElementEndNotConsumed(line)


class _BlockElementContainingInline_LineMarkOptionalEnd(
                                                _BlockElementContainingInline):
    """
    A block element, containing inline elements, that starts with a full-line
    mark and ends with an optional full-line mark.
    """
    START_MARK = None
    END_MARK = None

    def parse_first_line(self, line):
        match = self.START_MARK.fullmatch(line)
        if not match:
            raise _BlockElementStartNotMatched()
        indent = len(match.group(1))
        return (indent, indent, None)

    def check_last_line(self, line):
        match = self.END_MARK.fullmatch(line)
        if match:
            raise _BlockElementEndConsumed()
        if self.rawtext:
            raise _BlockElementEndNotConsumed(line)


class _BlockElementContainingInline_LineMarks(_BlockElementContainingInline):
    """
    A block element, containing inline elements, that starts and ends with
    full-line marks.
    """
    START_MARK = None
    END_MARK = None

    def parse_first_line(self, line):
        match = self.START_MARK.fullmatch(line)
        if not match:
            raise _BlockElementStartNotMatched()
        indent = len(match.group(1))
        return (indent, indent, None)

    def check_last_line(self, line):
        match = self.END_MARK.fullmatch(line)
        if match:
            raise _BlockElementEndConsumed()


class Paragraph(_BlockElementContainingInline):
    """
    A paragraph.

    The default container, it ends whenever an empty line is found. If multiple
    empty lines are found, all except the last one are considered part of the
    content.
    """
    HTML_TAGS = ('<p>', '</p>')

    def parse_first_line(self, line):
        if Marks.BLANK_LINE.fullmatch(line):
            raise _BlockElementStartNotMatched()
        indent = len(Marks.PARAGRAPH_INDENTATION.match(line).group())
        return (indent, indent, line[indent:])

    def check_last_line(self, line):
        element = self.find_element_start(line)
        if element:
            raise _BlockElementStartMatched(element)
        if Marks.BLANK_LINE.fullmatch(line):
            raise _BlockElementEndConsumed()

    def _add_raw_line(self, line):
        if line.startswith(Marks.BLOCK_ESCAPE):
            line = line[1:]
        super(Paragraph, self)._add_raw_line(line)

    def convert_to_html(self):
        html = self._trim_last_break(''.join(child.convert_to_html()
                                             for child in self.children))
        if len(self.parent.children) > 1:
            return html.join(self.HTML_TAGS)
        else:
            return html


class _BlockElementContainingText_LineMarks(_BlockElementContainingText):
    """
    A block element, containing plain text, that starts and ends with full-line
    marks.
    """
    START_MARK = None
    END_MARK = None

    def parse_first_line(self, line):
        match = self.START_MARK.fullmatch(line)
        if not match:
            raise _BlockElementStartNotMatched()
        indent = len(match.group(1))
        return (indent, indent, None)

    def check_last_line(self, line):
        match = self.END_MARK.fullmatch(line)
        if match:
            raise _BlockElementEndConsumed()


class _InlineElementContainingInline(_InlineElement):
    """
    Base class for inline elements containing inline elements.
    """
    @classmethod
    def install_marks(cls, start_mark_to_element, start_mark, end_mark):
        del start_mark_to_element[start_mark]
        cls.START_MARK_TO_INLINE_ELEMENT = start_mark_to_element
        cls.END_MARK = end_mark

    def convert_to_html(self):
        html = self._trim_last_break(''.join(child.convert_to_html()
                                             for child in self.children))
        return html.join(self.HTML_TAGS)


class _InlineElementContainingText(_InlineElement):
    """
    Base class for inline elements containing plain text.
    """
    @classmethod
    def install_marks(cls, start_mark_to_element, start_mark, end_mark):
        cls.START_MARK_TO_INLINE_ELEMENT = {}
        cls.END_MARK = end_mark

    def convert_to_html(self):
        return ''.join(child.convert_to_html() for child in self.children
                                                        ).join(self.HTML_TAGS)


class DummyInlineElement(_InlineElement):
    """
    Dummy inline element for parsing other inline elements.
    """
    @classmethod
    def install_marks(cls, start_mark_to_element, start_mark, end_mark):
        cls.START_MARK_TO_INLINE_ELEMENT = start_mark_to_element
        cls.END_MARK = None
