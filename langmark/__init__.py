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

# Inline elements must be installed by updating the following dictionary
#  directly from extension modules; for this reason they must be imported
#  *after* declaring it
INLINE_ELEMENTS = {}

from .elements import (headings, lists, code, formatting)

# The order of the block elements is important: put the most likey elements
#  first; some elements may rely on the fact that others have been discarded
# Additional extension modules should insert their block element classes in the
#  list below; they must thus be imported *after* importing langmark, but
#  *before* instantiating the Langmark class
BLOCK_ELEMENTS = [headings.Heading1Alt,
                  headings.Heading2Alt,
                  headings.Heading6,
                  headings.Heading5,
                  headings.Heading4,
                  headings.Heading3,
                  headings.Heading2,
                  headings.Heading1,
                  lists.UnorderedListItem,
                  code.FormattableCodeBlock,
                  code.PlainCodeBlock]


class Langmark:
    def __init__(self, stream):
        # The parameters for __init__ must reflect the attributes set through
        # argparse by the launcher script
        # TODO: Support passing a string instead of a stream

        elements._BlockElement.STREAM = stream
        elements._BlockElement.INSTALLED_BLOCK_ELEMENTS = BLOCK_ELEMENTS
        self.install_inline_elements()

        header = elements.Header()
        line = header.parse(stream)
        self.meta = header.keys
        self.etree = elements.Root(line)
        self.etree.parse_lines()

    def install_inline_elements(self):
        start_mark_to_element = {}
        element_to_compiled_marks = {}
        for Element in INLINE_ELEMENTS:
            marks = INLINE_ELEMENTS[Element]
            start_mark = re.compile(marks[0])
            try:
                end_mark = re.compile(marks[1])
            except IndexError:
                end_mark = start_mark
            start_mark_to_element[start_mark] = Element
            element_to_compiled_marks[Element] = (start_mark, end_mark)
        element_to_compiled_marks[elements.DummyInlineElement] = (None, None)
        # The first loop builds the dictionaries, which have to be installed
        #  in a separate loop
        for Element in element_to_compiled_marks:
            Element.install_marks(start_mark_to_element.copy(),
                                  *element_to_compiled_marks[Element])
