# -*- coding: utf-8 -*-
"""
READ AND WRITE FROM/TO []-HEADER text FILES
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

def line_to_tuple(line):
    """Converts a line text into a tuple.

    Parameters
    ----------

    line: str, a text line
    """
    return tuple(c.strip() for c in line.split())

def tuple_to_line(tup, sep=' '*4):
    """Converts a tuple into a line text. Values are separated by separator.

    Parameters
    ----------

    tup: tuple, to covert into a line text
    sep: str, separator 4-spaces by default
    """
    line = ''
    for i in tup[:-1]:
        line += str(i)
        line += sep
    return line + str(tup[-1])

class HeadedText():
    """Read and write sections of headed text files."""
    def __init__(self):
        self.sections = {}

    def read(self, fname):
        """Read a []-headed text file and store it as a dictionary, where:
        key = section name
        value = text lines.

        Parameters
        ----------
        fname: str, file name
        """
        file = open(fname, 'r', encoding='latin-1')
        secname = None
        for line in file:
            text = line[0:line.find(';')]
            if '[' in text:
                # CHANGE
                secname = text[text.find('[')+1:text.find(']')]
                if 'END' in text:
                    break
                else:
                    self.sections[secname] = []
            else:
                if text.strip():
                    self.sections[secname].append(text)

    def write(self, fname):
        """Write a []-headed text to file.

        Parameters
        ----------
        fname: str, file name.
        """
        file = open(fname, 'w')
        for section, lines in self.sections.items():
            file.write('[{}]\n'.format(section))
            for line in lines:
                file.write(line + '\n')
            file.write('\n')
        file.write('[END]\n')
        file.close()
