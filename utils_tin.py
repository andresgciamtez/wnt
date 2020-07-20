# -*- coding: utf-8 -*-

"""
TIN. Point elevations from a TIN stored in LandXML-1.2 format
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
__date__ = '2019-10-04'
__copyright__ = '(C) 2019 by Andrés García Martínez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import xml.etree.ElementTree as ET

ACCEPTABLE_DEVIATION = 1E-5

class Triangle:
    '''Triangle defined for 3 points, (xi, yi, zi).'''
    def __init__(self, p1, p2, p3):
        self.v1 = p1
        self.v2 = p2
        self.v3 = p3

    def xy_area(self):
        '''Calculate the XY area.'''
        a = self.v1[0]*(self.v2[1]-self.v3[1])
        a += self.v2[0]*(self.v3[1]-self.v1[1])
        a += self.v3[0]*(self.v1[1]-self.v2[1])
        return abs(a)/2

    def is_inside(self, point, tol=ACCEPTABLE_DEVIATION):
        '''Check if the point (x, y) is inside.'''
        a = self.xy_area()
        tmp = Triangle(self.v1, self.v2, point)
        a -= tmp.xy_area()
        tmp = Triangle(self.v3, self.v2, point)
        a -= tmp.xy_area()
        tmp = Triangle(self.v3, self.v1, point)
        a -= tmp.xy_area()
        return abs(a) <= tol

    def z(self, point):
        '''Return z corresponding to the point (x, y).'''
        a = self.v2[0] - self.v1[0]
        b = self.v2[1] - self.v1[1]
        c = self.v3[0] - self.v1[0]
        d = self.v3[1] - self.v1[1]
        e = self.v2[2] - self.v1[2]
        f = self.v3[2] - self.v1[2]
        det = a*d - b*c
        jx = (d*e - b*f)/det
        jy = (-c*e + a*f)/det
        dx = point[0] - self.v1[0]
        dy = (point[1] - self.v1[1])
        return jx*dx + jy*dy + self.v1[2]


class TIN:
    '''TIN surface.'''
    def __init__(self):
        self._faces = []
        self._points = {}

    def from_landxml(self, file, surfname=''):
        '''Load a TIN surface from a landXLM file.

        Parameters
        ----------
        file, string, is the LandXML file name
        surfname, string, is the surface name, by default load the first one
        '''
        sname = '{http://www.landxml.org/schema/LandXML-1.2}Surface'
        dname = '{http://www.landxml.org/schema/LandXML-1.2}Definition'
        tree = ET.parse(file)
        root = tree.getroot()
        for surface in root.iter(sname):
            if surface.find(dname).attrib['surfType'] == 'TIN':
                if surfname == '' or surfname == surface.attrib['name']:
                    for point in surface[1][0]:
                        y, x, z = tuple(map(float, point.text.split()))
                        self._points[point.attrib['id']] = x, y, z
                    for face in surface[1][1]:
                        self._faces.append(face.text.split())
                    break
        else:
            raise Exception('Incorrect name or none surface found.')

    def elevations(self, points):
        '''Return elevations [z1,..] from points [(x1, y1)..].
        '''
        result = []
        for p in points:
            for face in self._faces:
                v1, v2, v3 = [self._points[vertex] for vertex in face]
                t = Triangle(v1, v2, v3)
                if t.is_inside(p):
                    result.append(t.z(p))
                    break
            else:
                result.append(None)
        return result
