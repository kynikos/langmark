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
from . import (marks, elements)


class UnorderedListItem(elements._BlockElementContainingBlock_Prefix_Grouped):
    """
    An unordered list item::

        * List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    BLOCK_MARK = marks.BlockMarkPrefix(r'\*')
    HTML_OUTER_TAGS = ('<ul>', '</ul>')
    HTML_TAGS = ('<li>', '</li>')


class NumberedListItem(elements._BlockElementContainingBlock_Prefix_Grouped):
    """
    A numbered list item::

        #. List item
        1. List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    BLOCK_MARK = marks.BlockMarkPrefix(r'(?:[0-9]+|#)\.')
    HTML_OUTER_TAGS = ('<ol>', '</ol>')
    HTML_TAGS = ('<li>', '</li>')


class LatinListItem(elements._BlockElementContainingBlock_Prefix_Grouped):
    """
    An alphabetical list item using Latin characters::

        &. List item
        a. List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    # TODO: Let customize the class name
    BLOCK_MARK = marks.BlockMarkPrefix(r'[a-zA-Z&]\.')
    HTML_OUTER_TAGS = ('<ol class="langmark-latin">', '</ol>')
    HTML_TAGS = ('<li>', '</li>')
