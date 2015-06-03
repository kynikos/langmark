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

from .elements import (headings, lists, code, formatting)

# The order of the block elements is important: put the most likey elements
#  first; some elements may rely on the fact that others have been discarded
# Additional extension modules should insert their block element classes in the
#  list below; they must thus be imported *after* importing langmark, but
#  *before* instantiating the Langmark class
BLOCK_ELEMENTS = [headings.Heading1,
                  headings.Heading2,
                  headings.Heading3,
                  headings.Heading4,
                  headings.Heading5,
                  headings.Heading6,
                  lists.UnorderedListItem,
                  lists.NumberedListItem,
                  lists.LatinListItem,
                  code.FormattableCodeBlock,
                  code.PlainCodeBlock,
                  code.PlainTextBlock]

# The order of the inline elements is instead not important
# Additional extension modules should insert their inline element classes in
#  the list below; they must thus be imported *after* importing langmark, but
#  *before* instantiating the Langmark class
INLINE_ELEMENTS = [formatting.Emphasis,
                   formatting.Strong,
                   formatting.Superscript,
                   formatting.Subscript,
                   formatting.Small,
                   formatting.Strikethrough,
                   code.FormattableCode,
                   code.PlainCode,
                   code.PlainText]


class Langmark:
    def __init__(self):
        # The parameters for __init__ must reflect the attributes set through
        # argparse by the launcher script
        elements._BlockElement.INSTALLED_BLOCK_ELEMENTS = BLOCK_ELEMENTS
        self._install_inline_elements()

    def _install_inline_elements(self):
        start_mark_to_element = {}
        element_to_compiled_mark = {}
        for Element in INLINE_ELEMENTS:
            mark = Element.INLINE_MARK
            start_mark_to_element[mark.start] = Element
            element_to_compiled_mark[Element] = mark.start
        element_to_compiled_mark[elements.BaseInlineElement] = None
        # The first loop builds the dictionaries, which have to be installed
        #  in a separate loop
        for Element in element_to_compiled_mark:
            start_mark = element_to_compiled_mark[Element]
            try:
                Element.install_mark(start_mark_to_element.copy(), start_mark)
            except NotImplementedError:
                pass

    def parse(self, stream):
        # The parameters for parse must reflect the attributes set through
        # argparse by the launcher script
        # TODO: Support passing a string instead of a stream
        streamobj = elements.Stream(stream)
        header = elements.Header(streamobj)
        header.parse_next_line()
        self.meta = header.keys
        elements._BlockElement.STREAM = streamobj
        self.etree = elements.Root()
        self.etree.parse_tree()
