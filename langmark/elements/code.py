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

# This module is installed at the *bottom* of the file


class Marks(langmark.elements.Marks):
    FORMATTABLECODEBLOCK_START = re.compile(r'^\%{3,}[ \t]*$',
                                            flags=re.MULTILINE)
    FORMATTABLECODEBLOCK_END = re.compile(r'^\%{3,}[ \t]*\n',
                                            flags=re.MULTILINE)


class FormattableCodeBlock(
                        langmark.elements._BlockElementHostingInlineNoStrip):
    """
    A block of formattable monospace text.::

        %%%%
        Formatted code
        %%%%
    """
    HTML_TAGS = ('<pre>', '</pre>')

    @property
    def tree_bindings(self):
        return {Marks.FORMATTABLECODEBLOCK_END: self.close}

    @property
    def recursive_close_marks(self):
        return [Marks.FORMATTABLECODEBLOCK_END, ]

langmark.ADDITIONAL_ROOT_ELEMENTS.update({
                    Marks.FORMATTABLECODEBLOCK_START: FormattableCodeBlock})
