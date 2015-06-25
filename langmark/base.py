# Langmark - A powerful and extensible lightweight markup language.
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
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementContinue,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class Configuration:
    """
    Generic configuration parameters.
    """
    TAB_LENGTH = 4
    MARK_LIMIT = 3
    BLANK_LINE = re.compile(r'^[ \t]*\n')
    INDENTATION = re.compile(r'^[ \t]*')
    # If an inline mark has overlapping matches with an inline mark, **which
    #  should never happen by design**, it's impossible to only escape the
    #  block mark leaving the inline mark intact; if an escape character is
    #  added at the beginning of a line, it will always escape both.
    # If line breaks are disabled, enable the DOTALL version of ESCAPE_RE
    ESCAPE_RE = re.compile(r'`.')
    #ESCAPE_RE = re.compile(r'`.', re.DOTALL)
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

    def rewind_buffer(self):
        self.rewind_lines(*self.lines_buffer)


class RawText:
    """
    The content of an element.
    """
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

    @staticmethod
    def compute_equivalent_indentation(line):
        # TODO: Move to external library
        split = line.split('\t')
        indent = 0
        for chunk in split[:-1]:
            indent += len(chunk) // Configuration.TAB_LENGTH + 1
        indent *= Configuration.TAB_LENGTH
        indent += len(split[-1])
        return indent

    @staticmethod
    def trim_equivalent_indentation(indentation, line):
        # TODO: Move to external library
        current_indentation = 0
        for char in line:
            if char == '\t':
                rem = current_indentation % Configuration.TAB_LENGTH
                current_indentation += Configuration.TAB_LENGTH - rem
            else:
                current_indentation += 1
            if current_indentation >= indentation:
                return ' ' * (current_indentation - indentation - 1) + line[
                                                                indentation:]
        return line
