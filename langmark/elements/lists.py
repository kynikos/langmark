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


class UnorderedListItem(
                langmark.elements._BlockElementContainingBlock_Prefix_Grouped):
    """
    An unordered list item.::

        * List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    BLOCK_MARK = langmark.elements.BlockMarkPrefix('*')
    HTML_OUTER_TAGS = ('<ul>', '</ul>')
    HTML_TAGS = ('<li>', '</li>')
