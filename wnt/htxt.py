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

class Htxtf(object):
    """Read and write sections of headed txt files"""
    def __init__(self, fname):
        assert fexits(fname), 'I cannot find file: ' + fname
        self.file = open(fname, 'r')
        
    def __del__(self):
        self.file.close()
    
    def read(self):
        """Return a dictionary which keys are the section names, and the values
        the lines."""
        sections = {}
        secname = None
        for line in self.file:
            txt = line[0:line.find(';')]
            if '[' in txt:
                # CHANGE
                secname = txt[txt.find('[')+1:txt.find(']')]
                if 'END' in txt:
                    break
                else:
                    sections[secname] = []
            else:
                if len(txt.strip()) > 0:
                    sections[secname].append(txt)
        return sections
    
    def write(self, sections, fn):
        '''Write a []-headed txt to file'''
        f = open(fn, 'w')
        
        for section,lines in sections.items():
            f.write('[{}]\n'.format(section))
            for line in lines:
                f.write(line + '\n')
            
            f.write('\n')
        
        f.write('[END]\n')
        f.close()       
    
    def line_to_tuple(self, line):
        '''Converts a line text to a tuple'''
        return tuple( c.strip() for c in line.split())
    
    def tuple_to_line(self, tup, sep='    '):
        '''Converts a tuple to a line text. Values are separated by sep.'''
        line = ''
        for i in tup[:-1]:
            line += str(i)
            line += sep
        line += str(tup[-1])
        return line
