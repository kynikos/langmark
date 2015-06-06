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




class Configuration:
    """
    Auxiliary regular expressions and other constants.
    """
    TAB_LENGTH = 4
    MARK_LIMIT = 3
    BLANK_LINE = re.compile(r'^[ \t]*\n')
    INDENTATION = re.compile(r'^[ \t]*')
    # If an inline mark has overlapping matches with an inline mark, **which
    #  should never happen by design**, it's impossible to only escape the
    #  block mark leaving the inline mark intact; if an escape character is
    #  added at the beginning of a line, it will always escape both.
    ESCAPE_RE = re.compile(r'`.')
    PARAMETER_CHAR = re.escape(r'|')


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


class _Meta:
    """
    Base class for meta elements.
    """
    ATTRIBUTE_NAME = None


class Header(_Meta):
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
    ATTRIBUTE_NAME = 'header'
    # TODO: Support multiline metadata (using indentation for the continuation
    #       lines)
    METADATA = re.compile(r'^\:\:[ \t]*(.+?)(?:[ \t]+(.+?))?[ \t]*\n')

    def __init__(self):
        self.keys = {}
        self.parse_next_line()

    def parse_next_line(self):
        while True:
            line = _BlockElement.STREAM.read_next_line()
            match = self.METADATA.fullmatch(line)
            if match:
                self.keys[match.group(1)] = match.group(2)
                self.parse_next_line()
            else:
                # Inserting an emtpy line makes sure that elements starting
                #  with an empty line, like multiline headings, are recognized
                _BlockElement.STREAM.rewind_lines('\n', line)
                break


class _BlockMarkFactory:
    """
    Base class for block mark factories.
    """
    pass


class BlockMarkSimple(_BlockMarkFactory):
    """
    A simple sequence of the same character possibly only followed by
    whitespace characters.
    """
    START = r'^([ \t]*)({escaped_char}{{3,}})[ \t]*\n'
    END = r'[ \t]*\n'

    def __init__(self, char):
        # Make sure that char is a single character
        escaped_char = re.escape(char[0])
        self.start = re.compile(self.START.format(escaped_char=escaped_char))

    def make_end_mark(self, start_mark):
        return re.compile(re.escape(start_mark) + self.END)


class BlockMarkPrefix(_BlockMarkFactory):
    """
    A simple sequence of the same character possibly only followed by
    whitespace characters.
    """
    # Without the space after escaped_char there would be a clash with some
    #  inline elements at the start of a line
    PREFIX = r'^([ \t]*)({prefix}[ \t]+)(.*\n)'

    def __init__(self, regex):
        self.prefix = re.compile(self.PREFIX.format(prefix=regex))


class _InlineMarkFactory:
    """
    Base class for inline mark factories.
    """
    PREFIX_TEST = r'(?:(\n)|([ \t]?)|({escaped_char}))\Z'
    SUFFIX_TEST = r'[{escaped_char} \t]'
    POSSIBLE_MARK = r'({escaped_char}{quantifier})(?!{escaped_char}|$)([ \t])?'
    # All parameter marks should have the same capturing groups
    PARAMETER_MARK_NORMAL = r'({escaped_mark})(?!{escaped_char})'
    PARAMETER_MARK_SPACED = r'((?:^|[ \t]){escaped_mark})(?:[ \t]|$)'
    # All end marks should have the same capturing groups
    END_MARK_NORMAL = r'(?<!\n)({escaped_mark})(?!{escaped_char})'
    END_MARK_SPACED = r'([ \t]{escaped_mark})(?=[ \t]|$)'

    def __init__(self, start_char, end_char, max_chars):
        # Make sure that *_char are single characters
        self.escaped_start_char = re.escape(start_char[0])
        self.escaped_end_char = re.escape(end_char[0])
        # I also considered treating 1-character marks differently, making them
        #  work only if no whitespace is found between them; however this is
        #  very difficult to implement because the internal text still needs
        #  to be parsed for nested inline elements, and a white space should
        #  cancel all the parsing with an exception
        quantifier = r'{1,' + str(max_chars) + r'}' if max_chars else r'+'
        self.start = re.compile(self.POSSIBLE_MARK.format(
                escaped_char=self.escaped_start_char, quantifier=quantifier),
                re.MULTILINE)
        self.prefix_test = re.compile(self.PREFIX_TEST.format(
                        escaped_char=self.escaped_start_char), re.MULTILINE)
        self.suffix_test = re.compile(self.SUFFIX_TEST.format(
                        escaped_char=self.escaped_end_char), re.MULTILINE)

    def make_parameter_and_end_marks(self, parsed_text, start_mark,
                                     is_element_start):
        return self._make_marks(parsed_text, start_mark, is_element_start,
                                    self._make_parameter_and_end_marks_normal,
                                    self._make_parameter_and_end_marks_spaced)

    def make_end_mark(self, parsed_text, start_mark, is_element_start):
        return self._make_marks(parsed_text, start_mark, is_element_start,
                        self._make_end_mark_normal, self._make_end_mark_spaced)

    def _make_marks(self, parsed_text, start_mark, is_element_start,
                    _make_marks_normal, _make_marks_spaced):
        # Yes, most of this could be done directly in the regular expression,
        #  but good luck with that... Also remember that Python's standard re
        #  module doesn't support variable-length look-behind...
        line_start, pre_space, pre_char = self.prefix_test.search(parsed_text
                                                                    ).groups()
        if pre_char is not None:
            raise _InlineElementStartNotMatched()

        # There's no need to look for escaped characters: that's already done
        #  by the normal escaping algorithm, and every time a character is
        #  escaped, parsed_text is reset to start from the following unescaped
        #  character; also, an escape match will always start before a possible
        #  mark match, and they aren't allowed to overlap
        possible_mark, post_space = start_mark.groups()

        # I can't just match ^ to see if it's the start of a line, because
        #  in general parsed_text starts after the previous expression matched
        #  by the parser engine
        # Note that end marks at the end of lines are already excluded by the
        #  regular expression
        if is_element_start or line_start is not None:
            if post_space:
                # \n** text...
                return _make_marks_spaced(possible_mark)
            # \n**text...
            return _make_marks_normal(possible_mark)
        elif post_space:
            if pre_space:
                # ... ** text...
                return _make_marks_spaced(possible_mark)
            # ...** text...
            raise _InlineElementStartNotMatched()
        # ...**text...
        # ... **text...
        return _make_marks_normal(possible_mark)

    def _make_parameter_and_end_marks_normal(self, mark):
        parameter_mark = re.compile(self.PARAMETER_MARK_NORMAL.format(
                      escaped_mark=Configuration.PARAMETER_CHAR * len(mark),
                      escaped_char=Configuration.PARAMETER_CHAR),
                      re.MULTILINE)
        return (parameter_mark, self._make_end_mark_normal(mark))

    def _make_end_mark_normal(self, mark):
        return re.compile(self.END_MARK_NORMAL.format(
                          escaped_mark=self.escaped_end_char * len(mark),
                          escaped_char=self.escaped_end_char),
                          re.MULTILINE)

    def _make_parameter_and_end_marks_spaced(self, mark):
        # len(mark) is checked in _make_end_mark_spaced
        #if len(mark) > 1:
        parameter_mark = re.compile(self.PARAMETER_MARK_SPACED.format(
                      escaped_mark=Configuration.PARAMETER_CHAR * len(mark)),
                      re.MULTILINE)
        return (parameter_mark, self._make_end_mark_spaced(mark))

    def _make_end_mark_spaced(self, mark):
        if len(mark) > 1:
            return re.compile(self.END_MARK_SPACED.format(
                              escaped_mark=self.escaped_end_char * len(mark)),
                              re.MULTILINE)
        else:
            raise _InlineElementStartNotMatched()

    def check_parameter_mark(self, parsed_text, parameter_mark):
        try:
            return not parameter_mark.group(1)[0] == \
                            Configuration.PARAMETER_CHAR[-1] == parsed_text[-1]
        except IndexError:
            # parsed_text may be an empty string
            return True

    def check_end_mark(self, parsed_text, end_mark):
        if end_mark.group(1)[0] == self.escaped_end_char[-1]:
            try:
                pre_char = parsed_text[-1]
            except IndexError:
                pass
            else:
                if self.suffix_test.fullmatch(pre_char):
                    return False
        return True


class _InlineMarkEscapable(_InlineMarkFactory):
    """
    Base class for inline mark factories.
    """
    def __init__(self, char):
        _InlineMarkFactory.__init__(self, char, char, Configuration.MARK_LIMIT)


class _InlineMarkNonEscapable(_InlineMarkFactory):
    """
    Base class for inline mark factories.

    When it is not possible to escape the mark character with the normal escape
    character, allow an indefinite number of characters as a mark.
    """
    def __init__(self, char):
        _InlineMarkFactory.__init__(self, char, char, None)


class _InlineMarkEscapableEnd(_InlineMarkFactory):
    """
    Base class for inline mark factories.
    """
    def __init__(self, start_char, end_char):
        _InlineMarkFactory.__init__(self, start_char, end_char,
                                    Configuration.MARK_LIMIT)


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


class _InlineElementStartNotMatched(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    does not correspond to the start of the element.
    """
    pass


class _EndOfFile(Exception):
    """
    Internal exception used to communicate to the parent that the creation of
    an element has been stopped by the end of file.
    """
    pass


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
            lines = _BlockElement.STREAM.read_next_lines_buffered(
                                                        self.TEST_START_LINES)
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
            indent += len(chunk) // Configuration.TAB_LENGTH + 1
        indent *= Configuration.TAB_LENGTH
        indent += len(split[-1])
        return indent

    def find_element_start(self):
        for Element in self.INSTALLED_BLOCK_ELEMENTS:
            try:
                return Element()
            except (_BlockElementStartNotMatched, _EndOfFile):
                self._rewind_check_lines_buffer()
                continue
        return False

    def _parse_indentation(self, lines):
        raise NotImplementedError()

    def _parse_initial_lines(self, lines):
        raise NotImplementedError()

    def parse_next_line(self):
        raise NotImplementedError()

    def _rewind_check_lines_buffer(self):
        self.rewind_lines(*_BlockElement.STREAM.lines_buffer)

    def rewind_lines(self, *lines):
        _BlockElement.STREAM.rewind_lines(*lines)


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
    BLOCK_MARK = None

    def _parse_indentation(self, lines):
        match = self.BLOCK_MARK.prefix.fullmatch(lines[0])
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
        _BlockElementContainingBlock_Prefix.__init__(self)
        self.group_item_number = 0
        self.group_item_last = True

    def set_parent(self, element):
        super(_BlockElementContainingBlock_Prefix_Grouped, self).set_parent(
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
        self.end_mark = self.BLOCK_MARK.make_end_mark(match.group(2))
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
    def __init__(self):
        self.rawtext = RawText('')
        self.indentation_content = None
        _BlockElement.__init__(self)

    def _parse_indentation(self, lines):
        indentation, initial_lines = self.check_element_start(lines)
        return (indentation, '', initial_lines)

    def _add_raw_first_line(self, line):
        self.rawtext.append(line[self.indentation_external:])

    def _read_indented_test_end_lines(self, ignore_blank_lines):
        try:
            lines = _BlockElement.STREAM.read_next_lines_buffered(
                                                        self.TEST_END_LINES)
        except StopIteration:
            lines = _BlockElement.STREAM.lines_buffer
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
                    self.indentation_content = indentation
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
        dummyelement = BaseInlineElement(self, inline_parser, None, None, None)
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

    def __init__(self, parent, inline_parser, parsed_text, start_mark,
                 is_element_start):
        self.inline_parser = inline_parser
        self.inline_bindings = self.install_bindings(parsed_text, start_mark,
                                                            is_element_start)
        if self.ENABLE_ESCAPE:
            self.inline_bindings[Configuration.ESCAPE_RE] = \
                                                    self._handle_inline_escape
        _Element.__init__(self)
        self.set_parent(parent)

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
            self.children.append(RawText(event.parsed_text))
            self.parent.take_inline_control()
        else:
            self.children.append(RawText(''.join((event.parsed_text,
                                                  event.mark.group()))))

    def _handle_inline_parse_end(self, event):
        self.children.append(RawText(event.remainder_text))


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
            element = self.START_MARK_TO_INLINE_ELEMENT[event.regex](self,
                                        self.inline_parser, event.parsed_text,
                                        event.mark, not bool(self.children))
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
            self.parameters.append(self.children)
            self.children = []
        else:
            self.children.append(RawText(''.join((event.parsed_text,
                                                  event.mark.group()))))

    def get_parameters(self):
        # The last parameter is not appended to self.parameters
        return self.parameters + [self.children, ]


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
