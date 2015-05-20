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


class Marks(langmark.elements.Marks):
    # Without the space after the * there would be a clash with bold text at
    #  the start of a line
    UNORDEREDLISTITEM_START = re.compile(r'^(([ \t]*)\*[ \t]+)(.*\n)')


class UnorderedListItem(langmark.elements._BlockElementContainingBlock_Prefix):
    """
    An unordered list item.::

        * List item
    """
    START_MARK = Marks.UNORDEREDLISTITEM_START
    HTML_TAGS = ('<li>', '</li>')

    def __init__(self, *args, **kwargs):
        # Generalize ***********************************************************************
        # Execute *before* instantiating ********************************************
        self.INSTALLED_BLOCK_ELEMENTS = self.INSTALLED_BLOCK_ELEMENTS.copy()
        i = self.INSTALLED_BLOCK_ELEMENTS.index(UnorderedList)
        self.INSTALLED_BLOCK_ELEMENTS[i:i + 1] = [UnorderedListItem]
        super(UnorderedListItem, self).__init__(*args, **kwargs)


class UnorderedList(
                langmark.elements._BlockElementContainingBlock_Prefix_Group):
    """
    An unordered list.::

        * List item
        * List item
        * List item
    """
    # TODO: For the moment it's impossible to have two separate lists without
    #       other elements between them
    START_MARK = Marks.UNORDEREDLISTITEM_START  # Generalize *****************************
    INSTALLED_BLOCK_ELEMENTS = [UnorderedListItem, ]
    HTML_TAGS = ('<ul>', '</ul>')
