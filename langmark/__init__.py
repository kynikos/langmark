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

# The order of the elements is important: put the most likey elements first;
#  some elements may rely on the fact that others have been discarded
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
INLINE_ELEMENTS = [formatting.Emphasis,
                   formatting.Strong,
                   formatting.Superscript,
                   formatting.Subscript,
                   formatting.Small,
                   formatting.Strikethrough,
                   code.PlainCode,
                   code.FormattableCode]
# Extension modules should insert their Element classes in the lists above;
#  they must thus be imported *after* importing langmark, but *before*
#  instantiating the Langmark class


class Langmark:
    def __init__(self, stream):
        # The parameters for __init__ must reflect the attributes set through
        # argparse by the launcher script
        # TODO: Support passing a string instead of a stream

        elements._BlockElement.STREAM = stream

        # Install additional elements here
        elements._BlockElement.INSTALLED_BLOCK_ELEMENTS = BLOCK_ELEMENTS
        elements._InlineElement.INSTALLED_INLINE_ELEMENTS = INLINE_ELEMENTS

        header = elements.Header()
        line = header.parse(stream)
        self.meta = header.keys
        self.etree = elements.Root(line)
        self.etree.parse_lines()
