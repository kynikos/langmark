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

# Inline elements are installed at the bottom of this module


class Marks(langmark.elements.Marks):
    FORMATTABLECODEBLOCK_START = re.compile(r'^([ \t]*)\%{3,}[ \t]*\n')
    FORMATTABLECODEBLOCK_END = re.compile(r'^([ \t]*)\%{3,}[ \t]*\n')
    PLAINCODEBLOCK_START = re.compile(r'^([ \t]*)\#{3,}[ \t]*\n')
    PLAINCODEBLOCK_END = re.compile(r'^([ \t]*)\#{3,}[ \t]*\n')


class FormattableCode(langmark.elements._InlineElementContainingInline):
    """
    Inline formattable monospace text.::

        %%code%%
    """
    HTML_TAGS = ('<code>', '</code>')


class PlainCode(langmark.elements._InlineElementContainingText):
    """
    Inline preformatted monospace text.::

        ##code##
    """
    HTML_TAGS = ('<code>', '</code>')


class FormattableCodeBlock(
                    langmark.elements._BlockElementContainingInline_LineMarks):
    """
    A block of formattable monospace text.::

        %%%
        Formatted code
        %%%
    """
    START_MARK = Marks.FORMATTABLECODEBLOCK_START
    END_MARK = Marks.FORMATTABLECODEBLOCK_END
    HTML_TAGS = ('<pre>', '</pre>')


class PlainCodeBlock(langmark.elements._BlockElementContainingText_LineMarks):
    """
    A block of preformatted monospace text.::

        ###
        Plain code
        ###
    """
    START_MARK = Marks.PLAINCODEBLOCK_START
    END_MARK = Marks.PLAINCODEBLOCK_END
    HTML_TAGS = ('<pre>', '</pre>')

langmark.INLINE_ELEMENTS.update({FormattableCode: (r'%%', ),
                                 PlainCode: (r'##', )})
