#!/usr/bin/env python3

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

import argparse
from langmark import Langmark


def _parse_cli_args():
    cliparser = argparse.ArgumentParser(description="Langmark parser.",
                                        add_help=True)
    cliparser.add_argument('format', choices=['html'], metavar='FORMAT',
                        help='the output format, chosen among [%(choices)s]')
    cliparser.add_argument('source', metavar='SOURCE',
                        help='the file to be parsed')
    return cliparser.parse_args()


def main():
    cliargs = _parse_cli_args()
    doc = Langmark()
    with open(cliargs.source, 'r') as stream:
        doc.parse(stream)
    print({
        'html': doc.etree.convert_to_html,
    }[cliargs.format]())

if __name__ == '__main__':
    main()
