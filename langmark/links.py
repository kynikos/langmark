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
from . import (marks, metadata, elements)
from .base import RawText
from .factories import _MetaDataElementFactory
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class LinksData(metadata._MetaDataStorage):
    """
    Data on the links in the text.
    """
    ATTRIBUTE_NAME = 'links'

    def __init__(self, langmark_):
        metadata._MetaDataStorage.__init__(self, langmark_)
        self.id_to_data = {}

    def add_id(self, id_, url, title):
        self.id_to_data[id_] = (RawText(url),
                                RawText(title) if title else None)

    def get_data_html(self, id_):
        try:
            data = self.id_to_data[id_]
            url = data[0].convert_to_html()
            try:
                title = data[1].convert_to_html()
            except AttributeError:
                title = None
            return (url, title)
        except KeyError:
            # The passed value may not be a defined id
            raise ValueError


class Link(elements._InlineElementContainingParameters):
    """
    A link::

        [id]
        [url]
        [text|id]
        [text|url]
        [text|id|url]
        [text|id|url|title]
    """
    INLINE_MARK = marks._InlineMarkEscapableStartEnd('[', ']')
    HTML_TAGS = ('<a href="{href}">', '<a href="{href}" title="{title}">',
                 '</a>')

    def post_process_parameters(self):
        try:
            url = self.children[2].get_raw_text()
        except IndexError:
            return
        try:
            title = self.children[3].get_raw_text()
        except IndexError:
            title = None
        self.langmark.links.add_id(self.children[1].get_raw_text(), url, title)

    def convert_to_html(self):
        par1 = self.children[0]
        text = par1.convert_to_html()
        try:
            par2 = self.children[1]
        except IndexError:
            id_ = par1.get_raw_text()
            try:
                href, title = \
                    self.langmark.links.get_data_html(id_)
            except ValueError:
                href = text
                title = None
        else:
            id_ = par2.get_raw_text()
            try:
                href, title = \
                    self.langmark.links.get_data_html(id_)
            except ValueError:
                href = par2.convert_to_html()
                title = None
        if title:
            return text.join((self.HTML_TAGS[1].format(href=href,
                                      title=title), self.HTML_TAGS[2]))
        return text.join((self.HTML_TAGS[0].format(href=href),
                          self.HTML_TAGS[2]))


class LinkDefinitions(_MetaDataElementFactory):
    """
    Factory for link definitions::

        [id]: url Title
        [id]: url "Title"
    """
    TEST_START_LINES = 1
    METADATA = re.compile(r'^[ \t]*\[(.+?)\]:[ \t]+(.+?)'
                          r'(?:[ \t]+(?:\'(.+?)\'|"(.+?)"|\((.+?)\)|(.+?)))?'
                          r'[ \t]*\n')

    def process_match(self, langmark_, match):
        if not match:
            raise _BlockElementStartNotMatched()
        langmark_.links.add_id(match.group(1), match.group(2), match.group(3)
                        or match.group(4) or match.group(5) or match.group(6))
