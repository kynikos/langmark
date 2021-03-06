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
import textparser
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


class _Element:
    """
    Base class for document elements.
    """
    HTML_BREAK = '\n'

    def __init__(self, langmark_, parent):
        self.langmark = langmark_
        self.parent = parent
        self.children = []

    def read_lines(self, N):
        try:
            return self.langmark.stream.read_next_lines_buffered(N)
        except StopIteration:
            raise _EndOfFile()

    def read_lines_buffer(self):
        return self.langmark.stream.lines_buffer

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


class _BlockElement(_Element):
    """
    Base class for block elements.
    """
    TEST_END_LINES = None
    HTML_TAGS = ('<div>', '</div>')

    def __init__(self, langmark_, parent, indentation_external,
                 indentation_internal, initial_lines):
        _Element.__init__(self, langmark_, parent)
        self.indentation_external = indentation_external
        self.indentation_internal = indentation_internal
        self._process_initial_lines(initial_lines)

    def _process_initial_lines(self, lines):
        raise NotImplementedError()

    def parse_next_line(self):
        raise NotImplementedError()


class _BlockElementContainingBlock(_BlockElement):
    """
    Base class for elements containing block elements.
    """
    INSTALLED_BLOCK_FACTORIES = None

    def _process_initial_lines(self, lines):
        self.rewind_lines(*lines)

    def find_element_start(self):
        while True:
            try:
                for factory in self.INSTALLED_BLOCK_FACTORIES:
                    # Note how factory.make_element returns the element
                    #  by raising _BlockElementStartMatched
                    factory.make_element(self.langmark, self)
            except _BlockElementStartConsumed:
                # Restart the for loop from the beginning
                continue
            else:
                return False

    def parse_next_line(self):
        # Don't recurse, otherwise it will raise "RuntimeError: maximum
        #  recursion depth exceeded while calling a Python object" for long
        #  documents
        while True:
            try:
                self.find_element_start()
            except _BlockElementStartMatched as exc:
                element = exc.element
            except _BlockElementContinue as exc:
                if exc.element is self:
                    self.rewind_lines(*exc.lines)
                    continue
                else:
                    raise
            else:
                # find_element_start must *not* raise _BlockElementStartMatched
                #  also when the text would be a Paragraph, so paragraphs (the
                #  catch-all elements) must be created here
                try:
                    element = self.langmark.paragraph_factory.make_element(
                                                        self.langmark, self)
                except _BlockElementStartNotMatched:
                    # Just discard the consumed lines if really nothing wants
                    #  them
                    continue
                    # Don't recurse, otherwise it will raise "RuntimeError:
                    #  maximum recursion depth exceeded while calling a Python
                    #  object" for long documents
                    #self.parse_next_line()
                    #return
            # The element's parent may have been set to an ancestor of this
            #  object (self)
            if element.parent is self:
                # Use a loop instead of recursing, otherwise it will raise
                #  "RuntimeError: maximum recursion depth exceeded while
                #  calling a Python object" for long documents
                while True:
                    self.children.append(element)
                    try:
                        element.parse_next_line()
                    except _BlockElementEndConsumed:
                        break
                    except _BlockElementEndNotConsumed as exc:
                        self.rewind_lines(*exc.lines)
                        break
                    except _BlockElementStartMatched as exc:
                        # The element's parent may have been set to an ancestor
                        #  of this object (self)
                        if exc.element.parent is self:
                            element = exc.element
                            continue
                        else:
                            raise
                    except _BlockElementContinue as exc:
                        if exc.element is self:
                            self.rewind_lines(*exc.lines)
                            break
                        else:
                            raise
                    else:
                        break
            else:
                raise _BlockElementStartMatched(element)

    def convert_to_html(self):
        html = self.HTML_BREAK.join(child.convert_to_html()
                                    for child in self.children)
        if len(self.children) > 1:
            # TODO: Re-add the indentation before the tags
            return self.HTML_BREAK.join((self.HTML_TAGS[0], html,
                                         self.HTML_TAGS[1]))
        else:
            # self.children should never be empty, but still support the case
            return html.join(self.HTML_TAGS)


class Root(_BlockElementContainingBlock):
    """
    The root element of the tree.
    """
    def __init__(self, langmark_):
        _BlockElementContainingBlock.__init__(self, langmark_, None, 0, 0, ())

    def parse_tree(self):
        try:
            self.parse_next_line()
        except _EndOfFile:
            # _EndOfFile can be raised (and left uncaught) by Paragraph, for
            #  example if a document ends with a metadata element
            pass

    def convert_to_html(self):
        return self.HTML_BREAK.join(child.convert_to_html()
                                    for child in self.children)


class IndentedContainer(_BlockElementContainingBlock):
    """
    An indented block container.
    """
    HTML_TAGS = ('<div class="langmark-indented">', '</div>')


class _BlockElementContainingBlock_PrefixGrouped(_BlockElementContainingBlock):
    """
    Base class for block elements identified by a prefix that must be grouped
    inside an additional HTML element.
    """
    # TODO: This class should be made a mixin, but it's hard because of the
    #       super calls
    HTML_OUTER_TAGS = None

    def __init__(self, langmark_, parent, indentation_external,
                 indentation_internal, initial_lines):
        _BlockElementContainingBlock.__init__(self, langmark_, parent,
                    indentation_external, indentation_internal, initial_lines)
        self.group_item_number = 0
        self.group_item_last = True
        try:
            previous = parent.children[-1]
        except IndexError:
            # The list could be the first element of the document
            pass
        else:
            if previous.__class__ == self.__class__:
                self.group_item_number = previous.group_item_number + 1
                previous.group_item_last = False

    def convert_to_html(self):
        html = super(_BlockElementContainingBlock_PrefixGrouped,
                     self).convert_to_html()
        if self.group_item_number == 0:
            html = self.HTML_BREAK.join((self.HTML_OUTER_TAGS[0], html))
        if self.group_item_last is True:
            html = self.HTML_BREAK.join((html, self.HTML_OUTER_TAGS[1]))
        return html


class _BlockElementNotContainingBlock_LineMarksMixin:
    """
    Mixin class for block elements, containing inline elements, that start and
    end with full-line marks.
    """
    TEST_END_LINES = 1

    def set_end_mark(self, mark):
        self.end_mark = mark

    def _process_initial_lines(self, lines):
        pass

    def check_element_end(self, lines):
        if self.end_mark.fullmatch(lines[0]):
            raise _BlockElementEndConsumed()


class _BlockElementNotContainingBlock_EmptyLineMixin:
    """
    Mixin class for block elements, containing inline elements, that end with
    an empty line.
    """
    TEST_END_LINES = 1

    def _process_initial_lines(self, lines):
        self._add_raw_first_line(lines[0])

    def check_element_end(self, lines):
        if Configuration.BLANK_LINE.fullmatch(lines[0]):
            raise _BlockElementEndNotConsumed(*lines)


class _BlockElementNotContainingBlock(_BlockElement):
    """
    Base class for elements not containing block elements.
    """
    IGNORE_BLANK_LINES = None
    IGNORE_LEADING_SPACE = None

    def __init__(self, *args, **kwargs):
        self.rawtext = RawText('')
        _BlockElement.__init__(self, *args, **kwargs)

    def _add_raw_first_line(self, line):
        # Paragraph overrides this method
        self.rawtext.append(RawText.trim_equivalent_indentation(
                                            self.indentation_internal, line))

    def _read_indented_test_end_lines(self):
        try:
            lines = self.read_lines(self.TEST_END_LINES)
        except _EndOfFile:
            lines = self.read_lines_buffer()
            indented_lines = self._check_and_strip_indentation(lines)
            self._add_raw_content_lines(indented_lines)
            self._parse_inline()
            raise
        else:
            return self._check_and_strip_indentation(lines)

    def _check_and_strip_indentation(self, lines):
        indented_lines = []
        for lN, line in enumerate(lines):
            parent = self.parent
            while parent:
                try:
                    line = parent.preprocess_inline(line,
                                                    self.indentation_internal)
                    break
                except AttributeError:
                    parent = parent.parent
            if Configuration.BLANK_LINE.fullmatch(line):
                if not self.IGNORE_BLANK_LINES:
                    self._parse_inline()
                    raise _BlockElementEndNotConsumed(*lines[lN:])
                # Never strip the line break from blank lines
                indented_lines.append(RawText.trim_equivalent_indentation(
                            self.indentation_internal, line[:-1]) + line[-1])
            else:
                indentation = RawText.compute_equivalent_indentation(
                                Configuration.INDENTATION.match(line).group())
                if indentation < self.indentation_internal:
                    self._parse_inline()
                    raise _BlockElementEndNotConsumed(*lines[lN:])
                indented_line = RawText.trim_equivalent_indentation(
                                            self.indentation_internal, line)
                if self.IGNORE_LEADING_SPACE and indented_line.startswith(' '):
                    indented_line = indented_line[1:]
                indented_lines.append(indented_line)
        return indented_lines

    def _add_raw_content_lines(self, lines):
        self.rawtext.append(''.join(lines))

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

    The default container, it ends whenever an empty line is found.
    """
    TEST_END_LINES = 1
    IGNORE_BLANK_LINES = False
    IGNORE_LEADING_SPACE = True
    HTML_TAGS = ('<p>', '</p>')

    def _process_initial_lines(self, lines):
        self._add_raw_first_line(lines[0])

    def _add_raw_first_line(self, line):
        # Overrides superclass' method
        indented_line = RawText.trim_equivalent_indentation(
                                            self.indentation_internal, line)
        if indented_line.startswith(' '):
            indented_line = indented_line[1:]
        self.rawtext.append(indented_line)

    def parse_next_line(self):
        # Don't recurse, otherwise it will raise "RuntimeError: maximum
        #  recursion depth exceeded while calling a Python object" for long
        #  documents
        while True:
            try:
                # Use self.parent, otherwise if an element is found it will
                #  have the Paragraph as its parent
                self.parent.find_element_start()
            except _BlockElementStartMatched:
                self._parse_inline()
                raise
            except _BlockElementContinue as exc:
                if exc.element is self.parent:
                    self.rewind_lines(*exc.lines)
                    continue
                else:
                    self._parse_inline()
                    raise
            else:
                lines = self._read_indented_test_end_lines()
                self._add_raw_content_lines(lines)
                continue

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
    IGNORE_BLANK_LINES = True
    IGNORE_LEADING_SPACE = False

    def parse_next_line(self):
        # Don't recurse, otherwise it will raise "RuntimeError: maximum
        #  recursion depth exceeded while calling a Python object" for long
        #  documents
        while True:
            lines = self._read_indented_test_end_lines()
            try:
                self.check_element_end(lines)
            except (_BlockElementStartMatched, _BlockElementEndConsumed,
                    _BlockElementEndNotConsumed):
                self._parse_inline()
                raise
            else:
                self._add_raw_content_lines(lines)
                continue

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


class _BlockElementContainingInline_Indented(
                                _BlockElementNotContainingBlock_EmptyLineMixin,
                                _BlockElementContainingInline):
    """
    A block element, containing inline elements, whose start and end are
    only defined by indentation.
    """
    pass


class _BlockElementNotContainingInline(_BlockElementNotContainingBlock):
    """
    Base class for elements containing neither inline nor block elements.
    """
    IGNORE_BLANK_LINES = True
    IGNORE_LEADING_SPACE = False

    def parse_next_line(self):
        # Don't recurse, otherwise it will raise "RuntimeError: maximum
        #  recursion depth exceeded while calling a Python object" for long
        #  documents
        while True:
            lines = self._read_indented_test_end_lines()
            self.check_element_end(lines)
            self._add_raw_content_lines(lines)
            continue

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
        return self._trim_last_break(self.rawtext.get_raw_text())


class _BlockElementContainingRaw_EmptyLine(
                                _BlockElementNotContainingBlock_EmptyLineMixin,
                                _BlockElementNotContainingInline):
    """
    A block element, containing raw text, that ends with an empty line.
    marks.
    """
    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.get_raw_text())


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


class _BlockElementContainingText_Indented(
                                _BlockElementNotContainingBlock_EmptyLineMixin,
                                _BlockElementNotContainingInline):
    """
    A block element, containing plain text, whose start and end are only
    defined by indentation.
    """
    def convert_to_html(self):
        return self._trim_last_break(self.rawtext.convert_to_html()).join(
                                                                self.HTML_TAGS)


class HorizontalRule(_BlockElement):
    """
    A horizontal rule::

        ---
        _ _ _
        ~  ~  ~
        ===
        * * *
        +  +  +
    """
    # TODO: Allow setting the tag style (<hr> or <hr/> or <hr />) more easily
    HTML_TAG = '<hr />'

    def _process_initial_lines(self, lines):
        pass

    def parse_next_line(self):
        raise _BlockElementEndConsumed()

    def convert_to_html(self):
        return self.HTML_TAG


class _InlineElement(_Element):
    """
    Base class for inline elements.
    """
    ENABLE_ESCAPE = None
    START_MARK_TO_INLINE_ELEMENT = None
    INLINE_MARK = None
    HTML_TAGS = ('<span>', '</span>')

    def __init__(self, langmark_, parent, inline_parser, parsed_text,
                 start_mark, is_element_start):
        self.inline_parser = inline_parser
        self.inline_bindings = self.install_bindings(parsed_text, start_mark,
                                                            is_element_start)
        if self.ENABLE_ESCAPE:
            self.inline_bindings[Configuration.ESCAPE_RE] = \
                                                    self._handle_inline_escape
        _Element.__init__(self, langmark_, parent)

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
    def __init__(self, langmark_, parent, children):
        _Element.__init__(self, langmark_, parent)
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


class LineBreak(_Element):
    """
    A line break::

        First line`
        second line.
    """
    INLINE_MARK = marks._InlineMarkStartOnly(re.compile(r'`\n'))
    # TODO: Allow setting the tag style (<br> or <br/> or <br />) more easily
    HTML_TAG = '<br />'

    def __init__(self, langmark_, parent, inline_parser, parsed_text,
                 start_mark, is_element_start):
        _Element.__init__(self, langmark_, parent)
        self.parent.take_inline_control()

    def take_inline_control(self):
        pass

    def convert_to_html(self):
        return self.HTML_TAG + self.HTML_BREAK
