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


class _MetaDataStorage:
    """
    Base class for metadata-storing objects.
    """
    ATTRIBUTE_NAME = None

    def __init__(self, langmark):
        self.langmark = langmark


class Header(_MetaDataStorage):
    """
    The header of the document, hosting the meta data.
    """
    ATTRIBUTE_NAME = 'header'

    def __init__(self, langmark):
        _MetaDataStorage.__init__(self, langmark)
        self.keys = {}
