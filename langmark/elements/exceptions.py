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


class _BlockElementStartNotMatched(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    does not correspond to the start of the element.
    """
    pass


class _BlockElementStartConsumed(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    corresponds to the start of the element and has already been used.
    """
    pass


class _BlockElementStartMatched(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    corresponds to the start of a new element.
    """
    def __init__(self, element):
        self.element = element


class _BlockElementEndConsumed(Exception):
    """
    Internal exception used to communicate the end of the element to its
    parent. The parsed line has been consumed.
    """
    pass


class _BlockElementEndNotConsumed(Exception):
    """
    Internal exception used to communicate the end of the element to its
    parent. The parsed line must be consumed by the parent.
    """
    def __init__(self, *lines):
        self.lines = lines


class _InlineElementStartNotMatched(Exception):
    """
    Internal exception used to communicate to the parent that the parsed line
    does not correspond to the start of the element.
    """
    pass


class _EndOfFile(Exception):
    """
    Internal exception used to communicate to the parent that the creation of
    an element has been stopped by the end of file.
    """
    pass
