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
from .base import Configuration
from .exceptions import (_BlockElementStartNotMatched,
                         _BlockElementStartConsumed,
                         _BlockElementStartMatched,
                         _BlockElementEndConsumed,
                         _BlockElementEndNotConsumed,
                         _InlineElementStartNotMatched,
                         _EndOfFile)


class _BlockMarkFactory:
    """
    Base class for block mark factories.
    """
    pass


class BlockMarkSimple(_BlockMarkFactory):
    """
    A simple sequence of the same character possibly only followed by
    whitespace characters.
    """
    START = r'^([ \t]*)({escaped_char}{{3,}})[ \t]*\n'
    END = r'[ \t]*\n'

    def __init__(self, char):
        # Make sure that char is a single character
        escaped_char = re.escape(char[0])
        self.start = re.compile(self.START.format(escaped_char=escaped_char))

    def make_end_mark(self, start_mark):
        return re.compile(re.escape(start_mark) + self.END)


class BlockMarkPrefix(_BlockMarkFactory):
    """
    A simple sequence of the same character possibly only followed by
    whitespace characters.
    """
    # Without the space after escaped_char there would be a clash with some
    #  inline elements at the start of a line
    PREFIX = r'^([ \t]*)({prefix}[ \t]+)(.*\n)'

    def __init__(self, regex):
        self.prefix = re.compile(self.PREFIX.format(prefix=regex))


class _InlineMarkFactory:
    """
    Base class for inline mark factories.
    """
    pass


class _InlineMarkStartParametersEnd(_InlineMarkFactory):
    """
    Base class for inline mark factories.
    """
    PREFIX_TEST = r'(?:(\n)|([ \t]?)|({escaped_char}))\Z'
    SUFFIX_TEST = r'[{escaped_char} \t]'
    POSSIBLE_MARK = r'({escaped_char}{quantifier})(?!{escaped_char}|$)([ \t])?'
    # All parameter marks should have the same capturing groups
    PARAMETER_MARK_NORMAL = r'({escaped_mark})(?!{escaped_char})'
    PARAMETER_MARK_SPACED = r'((?:^|[ \t]){escaped_mark})(?:[ \t]|$)'
    # All end marks should have the same capturing groups
    END_MARK_NORMAL = r'(?<!\n)({escaped_mark})(?!{escaped_char})'
    END_MARK_SPACED = r'([ \t]{escaped_mark})(?=[ \t]|$)'

    def __init__(self, start_char, end_char, max_chars):
        # Make sure that *_char are single characters
        self.escaped_start_char = re.escape(start_char[0])
        self.escaped_end_char = re.escape(end_char[0])
        # I also considered treating 1-character marks differently, making them
        #  work only if no whitespace is found between them; however this is
        #  very difficult to implement because the internal text still needs
        #  to be parsed for nested inline elements, and a white space should
        #  cancel all the parsing with an exception
        quantifier = r'{1,' + str(max_chars) + r'}' if max_chars else r'+'
        self.start = re.compile(self.POSSIBLE_MARK.format(
                escaped_char=self.escaped_start_char, quantifier=quantifier),
                re.MULTILINE)
        self.prefix_test = re.compile(self.PREFIX_TEST.format(
                        escaped_char=self.escaped_start_char), re.MULTILINE)
        self.suffix_test = re.compile(self.SUFFIX_TEST.format(
                        escaped_char=self.escaped_end_char), re.MULTILINE)

    def make_parameter_and_end_marks(self, parsed_text, start_mark,
                                     is_element_start):
        return self._make_marks(parsed_text, start_mark, is_element_start,
                                    self._make_parameter_and_end_marks_normal,
                                    self._make_parameter_and_end_marks_spaced)

    def make_end_mark(self, parsed_text, start_mark, is_element_start):
        return self._make_marks(parsed_text, start_mark, is_element_start,
                        self._make_end_mark_normal, self._make_end_mark_spaced)

    def _make_marks(self, parsed_text, start_mark, is_element_start,
                    _make_marks_normal, _make_marks_spaced):
        # Yes, most of this could be done directly in the regular expression,
        #  but good luck with that... Also remember that Python's standard re
        #  module doesn't support variable-length look-behind...
        line_start, pre_space, pre_char = self.prefix_test.search(parsed_text
                                                                    ).groups()
        if pre_char is not None:
            raise _InlineElementStartNotMatched()

        # There's no need to look for escaped characters: that's already done
        #  by the normal escaping algorithm, and every time a character is
        #  escaped, parsed_text is reset to start from the following unescaped
        #  character; also, an escape match will always start before a possible
        #  mark match, and they aren't allowed to overlap
        possible_mark, post_space = start_mark.groups()

        # I can't just match ^ to see if it's the start of a line, because
        #  in general parsed_text starts after the previous expression matched
        #  by the parser engine
        # Note that end marks at the end of lines are already excluded by the
        #  regular expression
        if is_element_start or line_start is not None:
            if post_space:
                # \n** text...
                return _make_marks_spaced(possible_mark)
            # \n**text...
            return _make_marks_normal(possible_mark)
        elif post_space:
            if pre_space:
                # ... ** text...
                return _make_marks_spaced(possible_mark)
            # ...** text...
            raise _InlineElementStartNotMatched()
        # ...**text...
        # ... **text...
        return _make_marks_normal(possible_mark)

    def _make_parameter_and_end_marks_normal(self, mark):
        parameter_mark = re.compile(self.PARAMETER_MARK_NORMAL.format(
          escaped_mark=Configuration.PARAMETER_CHAR * len(mark),
          escaped_char=Configuration.PARAMETER_CHAR), re.MULTILINE)
        return (parameter_mark, self._make_end_mark_normal(mark))

    def _make_end_mark_normal(self, mark):
        return re.compile(self.END_MARK_NORMAL.format(
                          escaped_mark=self.escaped_end_char * len(mark),
                          escaped_char=self.escaped_end_char),
                          re.MULTILINE)

    def _make_parameter_and_end_marks_spaced(self, mark):
        # len(mark) is checked in _make_end_mark_spaced
        #if len(mark) > 1:
        parameter_mark = re.compile(self.PARAMETER_MARK_SPACED.format(
          escaped_mark=Configuration.PARAMETER_CHAR * len(mark)), re.MULTILINE)
        return (parameter_mark, self._make_end_mark_spaced(mark))

    def _make_end_mark_spaced(self, mark):
        if len(mark) > 1:
            return re.compile(self.END_MARK_SPACED.format(
                              escaped_mark=self.escaped_end_char * len(mark)),
                              re.MULTILINE)
        else:
            raise _InlineElementStartNotMatched()

    def check_parameter_mark(self, parsed_text, parameter_mark):
        try:
            return not parameter_mark.group(1)[0] == \
                            Configuration.PARAMETER_CHAR[-1] == parsed_text[-1]
        except IndexError:
            # parsed_text may be an empty string
            return True

    def check_end_mark(self, parsed_text, end_mark):
        if end_mark.group(1)[0] == self.escaped_end_char[-1]:
            try:
                pre_char = parsed_text[-1]
            except IndexError:
                pass
            else:
                if self.suffix_test.fullmatch(pre_char):
                    return False
        return True


class _InlineMarkEscapableSimple(_InlineMarkStartParametersEnd):
    """
    Base class for inline mark factories.
    """
    def __init__(self, char):
        _InlineMarkStartParametersEnd.__init__(self, char, char,
                                               Configuration.MARK_LIMIT)


class _InlineMarkNonEscapableSimple(_InlineMarkStartParametersEnd):
    """
    Base class for inline mark factories.

    When it is not possible to escape the mark character with the normal escape
    character, allow an indefinite number of characters as a mark.
    """
    def __init__(self, char):
        _InlineMarkStartParametersEnd.__init__(self, char, char, None)


class _InlineMarkEscapableStartEnd(_InlineMarkStartParametersEnd):
    """
    Base class for inline mark factories.
    """
    def __init__(self, start_char, end_char):
        _InlineMarkStartParametersEnd.__init__(self, start_char, end_char,
                                               Configuration.MARK_LIMIT)
