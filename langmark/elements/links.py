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


class LinksData(langmark.elements._MetaDataStorage):
    """
    The links data.
    """
    ATTRIBUTE_NAME = 'links'

    def __init__(self):
        self.id_to_element = {}

    def add_id(self, id_, element):
        self.id_to_element[id_] = element

    def get_href(self, id_):
        try:
            return self.id_to_element[id_].children[2]
        except KeyError:
            # The passed value may not be a defined id
            raise ValueError

    def get_title(self, id_):
        try:
            return self.id_to_element[id_].children[3]
        except KeyError:
            # The passed value may not be a defined id
            raise ValueError
        except IndexError:
            # The title is optional
            raise ValueError


class Link(langmark.elements._InlineElementContainingParameters):
    """
    A link.::

        [id]
        [url]
        [text|id]
        [text|url]
        [text|id|url]
        [text|id|url|title]
    """
    INLINE_MARK = langmark.elements._InlineMarkEscapableEnd('[', ']')
    HTML_TAGS = ('<a href="{href}">', '<a href="{href}" title="{title}">',
                 '</a>')

    def post_process_parameters(self):
        if len(self.children) > 2:
            langmark.elements._Element.DOCUMENT.links.add_id(
                                        self.children[1].get_raw_text(), self)

    def convert_to_html(self):
        title = None
        par1 = self.children[0]
        text = par1.convert_to_html()
        try:
            par2 = self.children[1]
        except IndexError:
            id_ = par1.get_raw_text()
            try:
                href = langmark.elements._Element.DOCUMENT.links.get_href(id_
                                                            ).convert_to_html()
            except ValueError:
                href = text
            else:
                try:
                    title = langmark.elements._Element.DOCUMENT.links.get_title(
                                                        id_).convert_to_html()
                except ValueError:
                    pass
        else:
            id_ = par2.get_raw_text()
            try:
                href = langmark.elements._Element.DOCUMENT.links.get_href(id_
                                                            ).convert_to_html()
            except ValueError:
                href = par2.convert_to_html()
            else:
                try:
                    title = langmark.elements._Element.DOCUMENT.links.get_title(
                                                        id_).convert_to_html()
                except ValueError:
                    pass
        if title:
            return text.join((self.HTML_TAGS[1].format(href=href,
                                      title=title), self.HTML_TAGS[2]))
        return text.join((self.HTML_TAGS[0].format(href=href),
                          self.HTML_TAGS[2]))
