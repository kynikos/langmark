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

import textparser

# Modules should update the following dictionaries with their installation
#  dictionaries
ADDITIONAL_ROOT_ELEMENTS = {}
ADDITIONAL_INLINE_ELEMENTS = {}
# Bundled extension modules must be imported *after* initializing the
#  *_ELEMENTS dictionaries above
from .elements import (headings, formatting, code)
# External extension modules must be imported *after* importing langmark, but
#  *before* instantiating the Langmark class


class Langmark:
    def __init__(self, text):
        # The parameters for __init__ must reflect the attributes set through
        # argparse by the launcher script

        # Install additional elements here
        elements.Root.install_elements(ADDITIONAL_ROOT_ELEMENTS)
        elements._InlineContainerElement.install_elements(
                                                    ADDITIONAL_INLINE_ELEMENTS)

        parser = textparser.TextParser(text)
        self.etree = elements.Root(parser)
        self.header = elements.Header(parser, self.etree)
        self.header.take_control()
        remainder_text = parser.parse()
        self.meta = self.header.keys
