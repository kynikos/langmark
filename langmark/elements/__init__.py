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


class Marks:
    META_START = re.compile(r'^\:\: *', flags=re.MULTILINE)
    META_SEPARATOR = re.compile(r' +')
    CONTENT_START = re.compile(r'^(?!\:\:)', flags=re.MULTILINE)
    LINE_BREAK = re.compile(r'\n', flags=re.MULTILINE)
    BLANK_LINE = re.compile(r'\n *\n', flags=re.MULTILINE)
    LINE_SECOND_CHAR = re.compile(r'(?<=^.)', flags=re.MULTILINE)


class _Element:
    def __init__(self, parser):
        self.parser = parser
        self.__bindings = self.init_bindings()

    def take_control(self):
        self.parser.reset_bindings(self.__bindings)
        self.parser.bind_to_parse_end(self._handle_parse_end)

    def init_bindings(self):
        raise NotImplementedError()

    def _handle_parse_end(self, event):
        raise NotImplementedError()


class Header(_Element):
    """
    The header of the file with the meta data.::

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

    def init_bindings(self):
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


class _TreeElement(_Element):
    HTML_BREAK = '\n'
    HTML_TAGS = ('<div>', '</div>')

    def __init__(self, parser, parent):
        super(_TreeElement, self).__init__(parser)
        self.parent = parent
        self.children = []

    def convert_to_html(self):
        html = self.HTML_TAGS[0]
        for child in self.children:
            try:
                html += child.convert_to_html()
            except AttributeError:
                html += child
        return html + self.HTML_TAGS[1]


class Root(_TreeElement):
    """
    The root element of the tree.

    The first section can start immediately after the header, or be separated
    by no more than one empty line.
    """
    def __init__(self, parser, root_elements):
        self.bindings = {Marks.LINE_SECOND_CHAR: self._handle_linesecondchar}
        self._install_elements(root_elements)
        # Instantiate the superclass *after* installing the elements
        super(Root, self).__init__(parser, None)

    def _install_elements(self, modules):
        for module in modules:
            for mark in module.INSTALLER:
                Element = module.INSTALLER[mark]
                handler = self._make_handler(Element)
                self.bindings[mark] = handler

    def _make_handler(self, Element):
        # Keep this method *separate* from self._install_elements's loops,
        #  because it has to have its own context!
        def handler(event):
            element = Element(self.parser, self)
            self.children.append(element)
            element.take_control()
        return handler

    def init_bindings(self):
        return self.bindings

    def _handle_linesecondchar(self, event):
        paragraph = Paragraph(self.parser, self, event.parsed_text)
        self.children.append(paragraph)
        paragraph.take_control()

    def convert_to_html(self):
        return self.HTML_BREAK.join(child.convert_to_html()
                                    for child in self.children)


class Paragraph(_TreeElement):
    """
    A paragraph.

    The default container, it ends whenever an empty line is found. If multiple
    empty lines are found, all except the last one are considered part of the
    content.
    """
    HTML_TAGS = ('<p>', '</p>')

    def __init__(self, parser, parent, parsed_text):
        super(Paragraph, self).__init__(parser, parent)
        self.parsed_text = parsed_text

    def init_bindings(self):
        return {Marks.BLANK_LINE: self._handle_paragraphend}

    def _handle_paragraphend(self, event):
        text = ''.join((self.parsed_text, event.parsed_text)).strip()
        self.children.append(text)
        self.parent.take_control()

    def _handle_parse_end(self, event):
        text = ''.join((self.parsed_text, event.remainder_text)).strip()
        self.children.append(text)
        self.parent.take_control()
