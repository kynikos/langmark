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
    EMPHASIS = re.compile(r'\'\'')
    STRONG = re.compile(r'\*\*')
    SUPERSCRIPT = re.compile(r'\^\^')
    SUBSCRIPT = re.compile(r',,')


class Emphasis(langmark.elements._InlineElementHostingInline):
    HTML_TAGS = ('<em>', '</em>')

    """
    Emphasized text (usually rendered with italic formatting).::

        ''emphasized''
    """
    @property
    def tree_bindings(self):
        return {Marks.EMPHASIS: self.close}


class Strong(langmark.elements._InlineElementHostingInline):
    HTML_TAGS = ('<strong>', '</strong>')

    """
    Important text (usually rendered with bold formatting).::

        **strong**
    """
    @property
    def tree_bindings(self):
        return {Marks.STRONG: self.close}


class Superscript(langmark.elements._InlineElementHostingInline):
    HTML_TAGS = ('<sup>', '</sup>')

    """
    Superscript text.::

        ^^superscript^^
    """
    @property
    def tree_bindings(self):
        return {Marks.SUPERSCRIPT: self.close}


class Subscript(langmark.elements._InlineElementHostingInline):
    HTML_TAGS = ('<sub>', '</sub>')

    """
    Subscript text.::

        **subscript**
    """
    @property
    def tree_bindings(self):
        return {Marks.SUBSCRIPT: self.close}

langmark.ADDITIONAL_INLINE_ELEMENTS.update({Marks.EMPHASIS: Emphasis,
                                            Marks.STRONG: Strong,
                                            Marks.SUPERSCRIPT: Superscript,
                                            Marks.SUBSCRIPT: Subscript})
