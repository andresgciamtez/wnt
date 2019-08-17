# -*- coding: utf-8 -*-
"""
READ AND WRITE FROM/TO []-HEADED TXT FILES
Andrés García Martínez (ppnoptimizer@gmail.com)
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Andrés García Martínez'
__date__ = '2019-07-19'
__copyright__ = '(C) 2019 by Andrés García Martínez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from os.path import exists as fexits

def line_to_tuple(line):
    """Converts a line text into a tuple.

    Parameters
    ----------

    line: str, a txt line
    """
    return tuple(c.strip() for c in line.split())

def tuple_to_line(tup, sep='    '):
    """Converts a tuple into a line text. Values are separated by separator.

    Parameters
    ----------

    tup: tuple, to covert into a line txt
    sep: str, separator 4-spaces by default
    """
    line = ''
    for i in tup[:-1]:
        line += str(i)
        line += sep
    return line + str(tup[-1])

class Htxtf():
    """Read and write sections of headed txt files."""
    def __init__(self):
        self.sections = {}

    def read(self, fname):
        """Read a []-headed txt file and store it as a dictionary, where:
        key = section name
        value = txt lines.

        Parameters
        ----------

        fname: str, file name
        """
        assert fexits(fname), 'I cannot find file: ' + fname
        file = open(fname, 'r')
        secname = None
        for line in file:
            txt = line[0:line.find(';')]
            if '[' in txt:
                # CHANGE
                secname = txt[txt.find('[')+1:txt.find(']')]
                if 'END' in txt:
                    break
                else:
                    self.sections[secname] = []
            else:
                if txt.strip():
                    self.sections[secname].append(txt)

    def write(self, fname):
        """Write a []-headed txt to file.

        Parameters
        ----------

        fname: str, file name.
        """
        f = open(fname, 'w')
        for section, lines in self.sections.items():
            f.write('[{}]\n'.format(section))
            for line in lines:
                f.write(line + '\n')
            f.write('\n')
        f.write('[END]\n')
        f.close()
