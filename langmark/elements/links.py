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


class Link(langmark.elements._InlineElementContainingParameters):
    """
    A link.::

        [idtext]
        [url]
        [text|id]
        [text|url]
    """
    INLINE_MARK = langmark.elements._InlineMarkEscapableEnd('[', ']')
    HTML_TAGS = ('<a href="{href}">', '</a>')

    def convert_to_html(self):
        parameters = self.get_parameters()
        value = ''.join(parameter.convert_to_html()
                        for parameter in parameters[0])
        try:
            href = ''.join(parameter.convert_to_html()
                           for parameter in parameters[1])
        except IndexError:
            href = value
        return value.join((self.HTML_TAGS[0].format(href=href),
                           self.HTML_TAGS[1]))
