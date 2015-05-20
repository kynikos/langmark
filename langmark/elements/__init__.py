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

# Class tree:
#
# _Element
#     Header
#     _TreeElement
#         _BlockElementHostingBlock
#             Root
#         _InlineContainerElement
#             _BlockElementHostingInlineStrip
#                 Paragraph
#                 headings.Heading*
#             _InlineContainerElementNoStrip
#                 _BlockElementHostingInlineNoStrip
#                     code.FormattableCodeBlock
#                 _InlineElementHostingInline
#                     formatting.*


class Marks:
    META_START = re.compile(r'^\:\:[ \t]*', flags=re.MULTILINE)
    META_SEPARATOR = re.compile(r'[ \t]+')
    CONTENT_START = re.compile(r'^(?!\:\:)', flags=re.MULTILINE)
    LINE_BREAK = re.compile(r'\n', flags=re.MULTILINE)
    BLANK_LINE = re.compile(r'\n[ \t]*\n', flags=re.MULTILINE)
    LINE_SECOND_CHAR = re.compile(r'(?<=^.)', flags=re.MULTILINE)


class _Element:
    """
    The most basic type of document element.
    """
    # Do *not* assign a default empty dict to INSTALLED_ELEMENTS, so that
    #  modules are forced to assign a *new* dict object to it through the
    #  install_elements class method; if modules simply updated/etc. a default
    #  dict, it would be modified for all classes, since they all derive from
    #  this class and in general do not redefine the attribute
    INSTALLED_ELEMENTS = None

    def __init__(self, parser):
        self.parser = parser
        self.__bindings = {}
        try:
            instelems = iter(self.INSTALLED_ELEMENTS)
        except TypeError:
            # No additional elements have been installed
            pass
        else:
            for mark in instelems:
                Element = self.INSTALLED_ELEMENTS[mark]
                handler = self.make_handler(Element)
                self.__bindings[mark] = handler
        # Read self.base_bindings *after* installing the additional elements,
        #  because classes must be able to override them
        self.__bindings.update(self.base_bindings)

    @classmethod
    def install_elements(cls, elements):
        # Do *not* extend/append/etc. to INSTALLED_ELEMENTS, see comment above
        cls.INSTALLED_ELEMENTS = elements

    def take_control(self):
        self.parser.reset_bindings(self.__bindings)
        self.parser.bind_to_parse_end(self.__handle_parse_end)

    def take_text_and_control(self, text):
        self.parser.prepend_text_and_reset_bindings(text, self.__bindings)
        self.parser.bind_to_parse_end(self.__handle_parse_end)

    def __handle_parse_end(self, event):
        event.parsed_text = event.remainder_text
        self.close(event)

    def make_handler(self, Element):
        # Keep this method *separate* from self.__init__'s loops also because
        #  it has to have its own context!
        # This method must be implemented (or a working implementation
        #  inherited) by all classes that need to support the installation of
        #  additional elements
        raise NotImplementedError()

    @property
    def base_bindings(self):
        raise NotImplementedError()

    def close(self, event):
        raise NotImplementedError()


class _TreeElement(_Element):
    """
    The most basic type of content element.
    """
    HTML_BREAK = '\n'
    HTML_TAGS = ('<div>', '</div>')

    def __init__(self, parser, parent):
        self.parent = parent
        self.children = []
        # Instantiate the superclass *after* storing parent and children, since
        #  especially parent may be required in self.tree_bindings properties,
        #  which are called in the superclass constructor
        super(_TreeElement, self).__init__(parser)

    @property
    def base_bindings(self):
        bindings = {mark: self.__close_recursive
                    for mark in self.recursive_close_marks}
        bindings.update(self.tree_bindings)
        return bindings

    @property
    def tree_bindings(self):
        raise NotImplementedError()

    @property
    def recursive_close_marks(self):
        return []

    def __close_recursive(self, event):
        self.children.append(event.parsed_text)
        self.parent.take_text_and_control(event.mark.group())

    def convert_to_html(self):
        raise NotImplementedError()


class _BlockElementHostingBlock(_TreeElement):
    """
    A block element that can only contain other block elements.
    """
    def make_handler(self, Element):
        def handler(event):
            element = Element(self.parser, self)
            self.children.append(element)
            element.take_control()
        return handler

    def convert_to_html(self):
        return self.HTML_BREAK.join(child.convert_to_html()
                                    for child in self.children)


class _InlineContainerElement(_TreeElement):
    """
    The base class for elements containing inline elements.
    """
    def convert_to_html(self):
        html = self.HTML_TAGS[0]
        for child in self.children:
            try:
                html += child.convert_to_html()
            except AttributeError:
                html += child
        return html + self.HTML_TAGS[1]


class _BlockElementHostingInlineStrip(_InlineContainerElement):
    """
    A block element that can only contain inline elements; it strips preceding
    and following whitespace.
    """
    def make_handler(self, Element):
        def handler(event):
            text = event.parsed_text if self.children \
                   else event.parsed_text.lstrip()
            self.children.append(text)
            element = Element(self.parser, self)
            self.children.append(element)
            element.take_control()
        return handler

    def close(self, event):
        text = event.parsed_text.rstrip() if self.children \
               else event.parsed_text.strip()
        self.children.append(text)
        self.parent.take_control()


class _InlineContainerElementNoStrip(_InlineContainerElement):
    """
    The base class for elements containing inline elements that do not strip
    whitespace around the text.
    """
    def make_handler(self, Element):
        def handler(event):
            self.children.append(event.parsed_text)
            element = Element(self.parser, self)
            self.children.append(element)
            element.take_control()
        return handler

    def close(self, event):
        self.children.append(event.parsed_text)
        self.parent.take_control()


class _BlockElementHostingInlineNoStrip(_InlineContainerElementNoStrip):
    """
    A block element that can only contain inline elements; it does not strip
    whitespace around the text.
    """
    pass


class _InlineElementHostingInline(_InlineContainerElementNoStrip):
    """
    An inline element that can contain other inline elements.
    """
    HTML_TAGS = ('<span>', '</span>')

    @property
    def recursive_close_marks(self):
        return self.parent.recursive_close_marks


class Header(_Element):
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
    def __init__(self, parser, etree):
        super(Header, self).__init__(parser)
        self.etree = etree
        self.keys = {}

    @property
    def base_bindings(self):
        return {Marks.META_START: self._handle_metastart,
                Marks.LINE_BREAK: self._handle_break,
                Marks.CONTENT_START: self._handle_contentstart}

    def _handle_metastart(self, event):
        # This handler also modifies the parsed_text that will be used in
        #  self.handle_break
        pass

    def _handle_break(self, event):
        key, value = Marks.META_SEPARATOR.split(event.parsed_text, maxsplit=1)
        self.keys[key] = value

    def _handle_contentstart(self, event):
        self.etree.take_control()


class Root(_BlockElementHostingBlock):
    """
    The root element of the tree.

    The first section can start immediately after the header, or be separated
    by no more than one empty line.
    """
    # TODO: Try to recognize root blocks that are not separated from the
    #       paragraph above with a blank line, for example:
    #
    #     Paragraph text.
    #     =======
    #     Heading
    #     =======
    #
    def __init__(self, parser):
        super(Root, self).__init__(parser, None)

    @property
    def tree_bindings(self):
        return {Marks.LINE_SECOND_CHAR: self._handle_linesecondchar}

    def _handle_linesecondchar(self, event):
        paragraph = Paragraph(self.parser, self)
        self.children.append(paragraph)
        paragraph.take_text_and_control(event.parsed_text)


class Paragraph(_BlockElementHostingInlineStrip):
    """
    A paragraph.

    The default container, it ends whenever an empty line is found. If multiple
    empty lines are found, all except the last one are considered part of the
    content.
    """
    HTML_TAGS = ('<p>', '</p>')

    @property
    def tree_bindings(self):
        return {Marks.BLANK_LINE: self.close}

    @property
    def recursive_close_marks(self):
        return [Marks.BLANK_LINE, ]
