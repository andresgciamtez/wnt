# -*- coding: utf-8 -*-
"""
SPLIT LINESTRINGS AS POITS
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

from math import copysign

def split_linestring(linestring, point, tol=0.0):
    """Split a line string at point.
    
    Return
    If exits intersection: ([(X0, Y0).. (Xs, Ys)], [(Xs, Ys).. (Xn, Yn)]);
                otherwise: None.

    Arguments
    ---------
    linestring: list, [(X0, Y0).. (Xn, Yn)] line string 
    point: tuple, (Xs, Ys) splitting point coordinates
    tol: float, tolerance distance
    """

    # SPLIT LINE STRING
    # SEGMENT LOOP
    n = len(linestring)-1
    for i in range(n):
        xs, ys = linestring[i][0:2]
        x1e, y1e = linestring[i+1][0]-xs, linestring[i+1][1]-ys
        x1p, y1p = point[0]-xs, point[1]-ys
        cteta = x1e / (x1e**2 + y1e**2)**0.5
        steta = copysign((1-cteta**2)**0.5, y1e)
        b = x1e*cteta + y1e*steta
        d = -x1p*steta + y1p*cteta
        a = x1p*cteta + y1p*steta
        xi = xs + a*cteta
        yi = ys + a*steta

        # IGNORE TOO SHORT SEGMENT
        if b > tol:
            # DETECT PROXIMITY
            if abs(d) <= tol:
                if -tol <= a <= tol:
                    if i == 0:
                        #print('Near start point')
                        return None # IGNORE INTERSECTION AT START POINT
                    # SPLIT AT INITIAL SEGMENT POINT
                    print('Splitted at vertex')
                    fpart = linestring[0:i+2].copy()
                    spart = linestring[i+1:].copy()
                    return (fpart, spart)
                if b-tol <= a <= b+tol:
                    if i == n-1:
                        #print('Near end point')
                        return None # IGNORE INTERSECTION AT END POINT
                    # SPLIT AT FINAL SEGMENT POINT
                    #print('Splitted at vertex')
                    fpart = linestring[0:i+2].copy()
                    spart = linestring[i+1:].copy()
                    return(fpart, spart)
                if tol < a < b-tol:
                    # SPLIT AT SEGMENT
                    #print('Splitted at inner point')
                    fpart = linestring[0:i+1].copy()
                    fpart.append((xi, yi))
                    spart = linestring[i+1:].copy()
                    spart.insert(0, (xi, yi))
                    return (fpart, spart)
        #else:
            #print('Too short segment')

    # SPLITTING POINT NOT FOUND
    return None

def split_linestring_m(linestring, points, tol=0.0):
    """Return a list of linestring parts splitted by points.

    The result is a list of list containing the linestring parts.
    [[initial_point, ..., first_division], ..., [last_division, final_point]]

    Arguments
    ---------
    linestring: list, [(x,y), ..]
    points: list, [(x, y), ..] splitting points
    tol: float, tolerance distance
    .
    
    """

    # INITIALIZE RESULT LINES
    result = [linestring.copy()]

    # POINTS LOOP
    for point in points:

        # LINESTRINGS LOOP
        for index, line in enumerate(result):
            # SPLIT
            splitted = split_linestring(line, point, tol)

            # CHANGE OLD LINE AND ADD NEW
            if splitted:
                result[index] = splitted[0]
                result.insert(index+1, splitted[1])
                break

    # RETURN RESULT
    return result
