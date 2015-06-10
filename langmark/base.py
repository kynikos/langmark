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
import itertools


class Configuration:
    """
    Auxiliary regular expressions and other constants.
    """
    TAB_LENGTH = 4
    MARK_LIMIT = 3
    BLANK_LINE = re.compile(r'^[ \t]*\n')
    INDENTATION = re.compile(r'^[ \t]*')
    # If an inline mark has overlapping matches with an inline mark, **which
    #  should never happen by design**, it's impossible to only escape the
    #  block mark leaving the inline mark intact; if an escape character is
    #  added at the beginning of a line, it will always escape both.
    ESCAPE_RE = re.compile(r'`.')
    PARAMETER_CHAR = re.escape(r'|')


class Stream:
    """
    The document stream.
    """
    def __init__(self, stream):
        self.stream = stream

    def read_next_line(self):
        # Do *not* use this method without protecting it from StopIteration
        #   and properly rewinding the parsed lines in case they aren't used!!!
        #  If possible, don't use this method at all (just rely on the core
        #   engine
        return next(self.stream)

    def read_next_lines_buffered(self, N):
        # Do *not* use this method without protecting it from StopIteration
        #   and properly rewinding the parsed lines in case they aren't used!!!
        #  If possible, don't use this method at all (just rely on the core
        #   engine
        self.lines_buffer = []
        # Don't use a list comprehension because StopIteration can be raised
        #  and the buffer must contain the last iterated lines
        for n in range(N):
            self.lines_buffer.append(self.read_next_line())
        return self.lines_buffer

    def rewind_lines(self, *lines):
        self.stream = itertools.chain(lines, self.stream)


class RawText:
    def __init__(self, text):
        self.text = text

    def append(self, text):
        self.text = ''.join((self.text, text))

    def get_raw_text(self):
        return self.text

    def convert_to_html(self):
        # "&" must be escaped *before* everything else
        text = self.text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        return text