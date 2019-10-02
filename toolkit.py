"""
ENTOOLKIT is a Phython Wrapper for EPANET Programmer's Toolkit
https://www.epa.gov/water-research/epanet
"""
import ctypes
import os
import sys
import platform
from pkg_resources import resource_filename

# SELECT OS AND PLATFORM
if os.name in ['nt', 'dos']:
    if '64' in platform.machine():
        LIB_FILE = 'epanet/Windows/%s.dll'%('epanet2_amd64')
    else:
        LIB_FILE = 'epanet/Windows/%s.dll'%('epanet2')

elif sys.platform in ['darwin']:
    LIB_FILE = 'epanet/Darwin/lib%s.dylib'%('epanet2')
else:
    LIB_FILE = 'epanet/Linux/lib%s.so'%('epanet')

_lib = ctypes.windll.LoadLibrary(resource_filename(__name__, LIB_FILE))

# DECLARE GENERAL CONSTANTS
MAX_LABEL_LEN = 15
ERR_MAX_CHAR = 80

def ENepanet(inpfn, rptfn='', binfn='', vfunc=None):
    """Runs a complete EPANET simulation.

    Arguments
    ---------
        inpfn: name of the input file
        rptfn: name of an output report file
        binfn: name of an optional binary output file
        vfunc: pointer to a user-supplied function which accepts a character
               string as its argument.
    """
    if vfunc is not None:
        cfunc = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
        callback = cfunc(vfunc)
    else:
        callback = None
    ierr = _lib.ENepanet(ctypes.c_char_p(inpfn.encode()),
                         ctypes.c_char_p(rptfn.encode()),
                         ctypes.c_char_p(binfn.encode()),
                         callback)
    if ierr:
        raise ENtoolkitError(ierr)


def ENopen(inpfn, rptfn='', binfn=''):
    """Opens the Toolkit to analyze a particular distribution system.

    Arguments
    ---------
        inpfn: name of the input file
        rptfn: name of an output report file
        binfn: name of an optional binary output file
    """
    ierr = _lib.ENopen(ctypes.c_char_p(inpfn.encode()),
                       ctypes.c_char_p(rptfn.encode()),
                       ctypes.c_char_p(binfn.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENclose():
    """Closes down the Toolkit system (including all files being processed)."""
    ierr = _lib.ENclose()
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetnodeindex(nodeid):
    """Return the index of a node with a specified ID.

    Arguments
    ---------
        nodeid: node ID label
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetnodeindex(ctypes.c_char_p(nodeid.encode()), ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetnodeid(index):
    """Return the ID label of a node with a specified index.

    Arguments
    ---------
        index: node index
    """
    label = ctypes.create_string_buffer(MAX_LABEL_LEN)
    ierr = _lib.ENgetnodeid(index, ctypes.byref(label))
    if ierr:
        raise ENtoolkitError(ierr)
    return label.value


def ENgetnodetype(index):
    """Return the node-type code for a specific node.

    Arguments
    ---------
        index: node index

        Node type codes:
        EN_JUNCTION  Junction node
        EN_RESERVOIR Reservoir node
        EN_TANK      Tank node
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetnodetype(index, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetnodevalue(index, paramcode):
    """Return the value of a specific node parameter.

    Arguments
    ---------
        index: node index
        paramcode: parameter code

        Node parameter codes:
        EN_ELEVATION  Elevation
        EN_BASEDEMAND ** Base demand
        EN_PATTERN    ** Demand pattern index
        EN_EMITTER    Emitter coeff.
        EN_INITQUAL   Initial quality
        EN_SOURCEQUAL Source quality
        EN_SOURCEPAT  Source pattern index
        EN_SOURCETYPE Source type (See note below)
        EN_DEMAND     * Actual demand
        EN_HEAD       * Hydraulic head
        EN_PRESSURE   * Pressure
        EN_QUALITY    * Actual quality
        EN_SOURCEMASS * Mass flow rate per minute of a chemical source
        * computed values
        ** primary demand category is last on demand list

        The following parameter codes apply only to storage tank nodes:
        EN_TANKLEVEL   Initial water level in tank
        EN_INITVOLUME  Initial water volume
        EN_MIXMODEL    Mixing model code (see below)
        EN_MIXZONEVOL  Inlet/Outlet zone volume in a 2-compartment tank
        EN_TANKDIAM    Tank diameter
        EN_MINVOLUME   Minimum water volume
        EN_VOLCURVE    Index of volume versus depth curve (0 if none assigned)
        EN_MINLEVEL    Minimum water level
        EN_MAXLEVEL    Maximum water level
        EN_MIXFRACTION Fraction of total volume occupied by the inlet/outlet
                       zone in a 2-compartment tank
        EN_TANK_KBULK  Bulk reaction rate coefficient
        """
    j = ctypes.c_float()
    ierr = _lib.ENgetnodevalue(index, paramcode, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetlinkindex(linkid):
    """Return the index of a link with a specified ID.

    Arguments
    ---------
        linkid: link ID label
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetlinkindex(ctypes.c_char_p(linkid.encode()), ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetlinkid(index):
    """Return the ID label of a link with a specified index.

    Arguments
    ---------
        index: link index
    """
    label = ctypes.create_string_buffer(MAX_LABEL_LEN)
    ierr = _lib.ENgetlinkid(index, ctypes.byref(label))
    if ierr:
        raise ENtoolkitError(ierr)
    return label.value


def ENgetlinktype(index):
    """Return the link-type code for a specific link.

    Arguments
    ---------
        index: link index

        Link type codes:
        EN_CVPIPE Pipe with Check Valve
        EN_PIPE   Pipe
        EN_PUMP   Pump
        EN_PRV    Pressure Reducing Valve
        EN_PSV    Pressure Sustaining Valve
        EN_PBV    Pressure Breaker Valve
        EN_FCV    Flow Control Valve
        EN_TCV    Throttle Control Valve
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetlinktype(index, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetlinknodes(index):
    """Return the indexes of the end nodes (start, end) of a specified link.

    Arguments
    ---------
        index: link index
    """
    j1 = ctypes.c_int()
    j2 = ctypes.c_int()
    ierr = _lib.ENgetlinknodes(index, ctypes.byref(j1), ctypes.byref(j2))
    if ierr:
        raise ENtoolkitError(ierr)
    return j1.value, j2.value

def ENgetlinkvalue(index, paramcode):
    """Return the value of a specific link parameter.

    Arguments
    ---------
        index:     link index
        paramcode: link parameter code

        Link parameter codes:
        EN_DIAMETER     Diameter
        EN_LENGTH       Length
        EN_ROUGHNESS    Roughness coeff.
        EN_MINORLOSS    Minor loss coeff.
        EN_INITSTATUS   Initial link status (0 = closed, 1 = open)
        EN_INITSETTING  Roughness for pipes, initial speed for pumps,initial
                        setting for valves
        EN_KBULK        Bulk reaction coeff.
        EN_KWALL        Wall reaction coeff.
        EN_FLOW         * Flow rate
        EN_VELOCITY     * Flow velocity
        EN_HEADLOSS     * Head loss
        EN_STATUS       * Actual link status (0 = closed, 1 = open)
        EN_SETTING      * Roughness for pipes, actual speed for pumps, actual
                        setting for valves
        EN_ENERGY       * Energy expended in kwatts
        * computed values
    """
    j = ctypes.c_float()
    ierr = _lib.ENgetlinkvalue(index, paramcode, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetpatternid(index):
    """Return the ID label of a particular time pattern.

    Arguments
    ---------
        index: pattern index
    """
    label = ctypes.create_string_buffer(MAX_LABEL_LEN)
    ierr = _lib.ENgetpatternid(index, ctypes.byref(label))
    if ierr:
        raise ENtoolkitError(ierr)
    return label.value

def ENgetpatternindex(patternid):
    """Return the index of a particular time pattern.

    Arguments
    ---------
        id: pattern ID label
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetpatternindex(ctypes.c_char_p(patternid.encode()), ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetpatternlen(index):
    """Return the number of time periods in a specific time pattern.

    Arguments
    ---------
        index:pattern index
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetpatternlen(index, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetpatternvalue(index, period):
    """Return the multiplier factor for a specific time period in a time pattern.

    Arguments
    ---------
        index:  time pattern index
        period: period within time pattern
    """
    j = ctypes.c_float()
    ierr = _lib.ENgetpatternvalue(index, period, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetcontrol(cindex, ctype, lindex, setting, nindex, level):
    """return the parameters of a simple control statement.

    Arguments
    ---------
       cindex:  control statement index
       ctype:   control type code EN_LOWLEVEL   (Low Level Control)
                                  EN_HILEVEL    (High Level Control)
                                  EN_TIMER      (Timer Control)
                                  EN_TIMEOFDAY  (Time-of-Day Control)
       lindex:  index of link being controlled
       setting: value of the control setting
       nindex:  index of controlling node
       level:   value of controlling water level or pressure for level controls
                or of time of control action (in seconds) for time-based controls.
    """
    ierr = _lib.ENgetcontrol(ctypes.c_int(cindex), ctypes.c_int(ctype),
                             ctypes.c_int(lindex), ctypes.c_float(setting),
                             ctypes.c_int(nindex), ctypes.c_float(level))
    if ierr:
        raise ENtoolkitError(ierr)
    return cindex, ctype, lindex, setting, nindex, level




def ENgetcount(countcode):
    """Return the number of network components of a specified type.

    Arguments
    ---------
        countcode: component code

        Component codes:
        EN_NODECOUNT    Nodes
        EN_TANKCOUNT    Reservoir and tank nodes
        EN_LINKCOUNT    Links
        EN_PATCOUNT     Time patterns
        EN_CURVECOUNT   Curves
        EN_CONTROLCOUNT Simple controls
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetcount(countcode, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetflowunits():
    """Return a code number indicating the units used to express all flow rates.

        Flow units codes:
        EN_CFS  Cubic feet per second
        EN_GPM  Gallons per minute
        EN_MGD  Million gallons per day
        EN_IMGD Imperial mgd
        EN_AFD  Acre-feet per day
        EN_LPS  Liters per second
        EN_LPM  Liters per minute
        EN_MLD  Million liters per day
        EN_CMH  Cubic meters per hour
        EN_CMD  Cubic meters per day
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetflowunits(ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgettimeparam(paramcode):
    """Return the value of a specific analysis time parameter.

    Arguments
    ---------
    paramcode: EN_DURATION     Simulation duration
               EN_HYDSTEP      Hydraulic time step
               EN_QUALSTEP     Water quality time step
               EN_PATTERNSTEP  Time pattern time step
               EN_PATTERNSTART Time pattern start time
               EN_REPORTSTEP   Reporting time step
               EN_REPORTSTART  Report starting time
               EN_RULESTEP     Time step for evaluating rule-based controls
               EN_STATISTIC    Type of time series post-processing used:
                   * Type of time series post-processing used:
                   EN_AVERAGE  Averaged
                   EN_MINIMUM  Minimums
                   EN_MAXIMUM  Maximus
                   EN_RANGE    Ranges
              EN_PERIODS      cNumber of reporting periods saved to binary file
    """
    j = ctypes.c_int()
    ierr = _lib.ENgettimeparam(paramcode, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def  ENgetqualtype(qualcode, tracenode):
    """Return the type of water quality analysis and the trace node.

     qualcode: EN_NONE    No quality analysis
               EN_CHEM    Chemical analysis
               EN_AGE     Water age analysis
               EN_TRACE   Source tracing

    tracenode: index of node traced in a source tracing analysis (value will be
               0 when qualcode is not EN_TRACE).
    """
    qualcode = ctypes.c_int()
    tracenode = ctypes.c_int()
    ierr = _lib.ENgetqualtype(ctypes.byref(qualcode),
                              ctypes.byref(tracenode))
    if ierr:
        raise ENtoolkitError(ierr)
    return qualcode.value, tracenode.value


def ENgetoption(optioncode):
    """Return the value of a particular analysis option.

    Arguments
    ---------
    optioncode: EN_TRIALS
                EN_ACCURACY
                EN_TOLERANCE
                EN_EMITEXPON
                EN_DEMANDMULT
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetoption(optioncode, ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENgetversion():
    """Return the current version number of the Toolkit.
    """
    j = ctypes.c_int()
    ierr = _lib.ENgetversion(ctypes.byref(j))
    if ierr:
        raise ENtoolkitError(ierr)
    return j.value


def ENsetcontrol(cindex, ctype, lindex, setting, nindex, level):
    """Sets the parameters of a simple control statement.

    Arguments
    ---------
       cindex: control statement index
       ctype: control type code EN_LOWLEVEL   (Low Level Control)
                                EN_HILEVEL    (High Level Control)
                                EN_TIMER      (Timer Control)
                                EN_TIMEOFDAY  (Time-of-Day Control)
       lindex:  index of link being controlled
       setting: value of the control setting
       nindex:  index of controlling node
       level:   value of controlling water level or pressure for level controls
                or of time of control action (in seconds) for time-based controls.
    """
    ierr = _lib.ENsetcontrol(ctypes.c_int(cindex),
                             ctypes.c_int(ctype),
                             ctypes.c_int(lindex),
                             ctypes.c_float(setting),
                             ctypes.c_int(nindex),
                             ctypes.c_float(level))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetnodevalue(index, paramcode, value):
    """Sets the value of a parameter for a specific node.

    Arguments
    ---------
        index: node index
        paramcode: node parameter
        value: parameter value

        Node parameter codes:
        EN_ELEVATION  Elevation
        EN_BASEDEMAND ** Base demand
        EN_PATTERN    ** Demand pattern index
        EN_EMITTER    Emitter coeff.
        EN_INITQUAL   Initial quality
        EN_SOURCEQUAL Source quality
        EN_SOURCEPAT  Source pattern index
        EN_SOURCETYPE Source type (See note below)
        EN_TANKLEVEL  Initial water level in tank
        ** primary demand category is last on demand list

        The following parameter codes apply only to storage tank nodes
        EN_TANKDIAM      Tank diameter
        EN_MINVOLUME     Minimum water volume
        EN_MINLEVEL      Minimum water level
        EN_MAXLEVEL      Maximum water level
        EN_MIXMODEL      Mixing model code
        EN_MIXFRACTION   Fraction of total volume occupied by the inlet/outlet
        EN_TANK_KBULK    Bulk reaction rate coefficient
    """
    ierr = _lib.ENsetnodevalue(ctypes.c_int(index),
                               ctypes.c_int(paramcode),
                               ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetlinkvalue(index, paramcode, value):
    """Sets the value of a parameter for a specific link.

    Arguments
    ---------
        index:  link index
        paramcode: parameter code
        value: parameter value

        Link parameter codes:
        EN_DIAMETER     Diameter
        EN_LENGTH       Length
        EN_ROUGHNESS    Roughness coeff
        EN_MINORLOSS    Minor loss coeff
        EN_INITSTATUS   * Initial link status (0 = closed, 1 = open)
        EN_INITSETTING  * Roughness for pipes, initial speed for pumps, initial
                        setting for valves
        EN_KBULK        Bulk reaction coeff
        EN_KWALL        Wall reaction coeff
        EN_STATUS       * Actual link status (0 = closed, 1 = open)
        EN_SETTING      * Roughness for pipes, actual speed for pumps, actual
                        setting for valves
    * Use EN_INITSTATUS and EN_INITSETTING to set the design value for a link's
    status or setting that exists prior to the start of a simulation. Use
    EN_STATUS and EN_SETTING to change these values while a simulation is being
    run (within the ENrunH - ENnextH loop).
    """
    ierr = _lib.ENsetlinkvalue(ctypes.c_int(index), ctypes.c_int(paramcode),
                               ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetpattern(index, factors):
    """Sets all of the multiplier factors for a specific time pattern.

    Arguments
    ---------
        index:   time pattern index
        factors: multiplier factors list for the entire pattern
    """
    nfactors = len(factors)
    cfactors_type = ctypes.c_float* nfactors
    cfactors = cfactors_type()
    for i in range(nfactors):
        cfactors[i] = float(factors[i])
    ierr = _lib.ENsetpattern(ctypes.c_int(index),
                             cfactors,
                             ctypes.c_int(nfactors))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetpatternvalue(index, period, value):
    """Sets the multiplier factor for a specific period within a time pattern.

    Arguments
    ---------
       index:  time pattern index
       period: period within time pattern
       value:  multiplier factor for the period
      """

    ierr = _lib.ENsetpatternvalue(ctypes.c_int(index), ctypes.c_int(period),
                                  ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetqualtype(qualcode, chemname, chemunits, tracenode):
    """Sets the type of water quality analysis called for.

    Arguments
    ---------
        qualcode:   water quality analysis code
        chemname:   name of the chemical being analyzed
        chemunits:  units that the chemical is measured in
        tracenode:  ID of node traced in a source tracing analysis

        Water quality analysis codes:
        EN_NONE  No quality analysis
        EN_CHEM  Chemical analysis
        EN_AGE   Water age analysis
        EN_TRACE Source tracing
    """
    ierr = _lib.ENsetqualtype(ctypes.c_int(qualcode),
                              ctypes.c_char_p(chemname.encode()),
                              ctypes.c_char_p(chemunits.encode()),
                              ctypes.c_char_p(tracenode.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def  ENsettimeparam(paramcode, timevalue):
    """Sets the value of a time parameter.

    Arguments
    ---------
        paramcode: time parameter code
        timevalue: value of time parameter in seconds/statistic type

        Time parameter codes:
        EN_DURATION
        EN_HYDSTEP
        EN_QUALSTEP
        EN_PATTERNSTEP
        EN_PATTERNSTART
        EN_REPORTSTEP
        EN_REPORTSTART
        EN_RULESTEP
        EN_STATISTIC
        EN_PERIODS

        Statistic type constants:
        EN_AVERAGE  averaged
        EN_MINIMUM  minimums
        EN_MAXIMUM  maximums
        EN_RANGE    ranges
    """
    ierr = _lib.ENsettimeparam(ctypes.c_int(paramcode), ctypes.c_int(timevalue))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetoption(optioncode, value):
    """Sets the value of a particular analysis option.

    Arguments
    ---------
        optioncode: option code EN_TRIALS
                                EN_ACCURACY
                                EN_TOLERANCE
                                EN_EMITEXPON
                                EN_DEMANDMULT
        value:  option value
      """
    ierr = _lib.ENsetoption(ctypes.c_int(optioncode), ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsavehydfile(fname):
    """Saves the current contents of the binary hydraulics file to a file.

    Arguments
    ---------
    fname: name of the file where the hydraulics results should be saved

    """
    ierr = _lib.ENsavehydfile(ctypes.c_char_p(fname.encode()))
    if ierr:
        raise ENtoolkitError(ierr)

def  ENusehydfile(fname):
    """Uses the contents of the specified file as the current binary hydraulics
    file.

    Arguments
    ---------
    fname: name of the file containing hydraulic analysis results for the
           current network
    """
    ierr = _lib.ENusehydfile(ctypes.c_char_p(fname.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsolveH():
    """Runs a complete hydraulic simulation with results for all time periods
    written to the binary Hydraulics file.
    """
    ierr = _lib.ENsolveH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENopenH():
    """Opens the hydraulics analysis system.
    """
    ierr = _lib.ENopenH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENinitH(flag=None):
    """Initializes storage tank levels, link status and settings, and the
    simulation clock time prior to running a hydraulic analysis.

    Arguments
    ---------
        flag:  two-digit flag indicating if hydraulic results will be saved to
                the hydraulics file (rightmost digit) and if link flows should
                be re-initialized.

    EN_NOSAVE           do not re-initialize flows, do not save results to file
    EN_SAVE             do not re-initialize flows, save results to file
    EN_INITFLOW         re-initialize flows, do not save results to file
    EN_SAVE+EN_INITFLOW re-initialize flows, save results to file
    """
    ierr = _lib.ENinitH(flag)
    if ierr:
        raise ENtoolkitError(ierr)


def ENrunH():
    """Return the current simulation clock time t in seconds.

    Runs a single period hydraulic analysis. First step in ENrunH - ENnextH loop.
    """
    t = ctypes.c_long()
    ierr = _lib.ENrunH(ctypes.byref(t))
    if ierr >= 100: # ierr < 100 WARNING
        raise ENtoolkitError(ierr)
    return t.value


def ENnextH():
    """Return the time (in seconds) until next hydraulic event occurs or 0 if
    at the end of the simulation period.

    Advances the hydraulic simulation to the start of the next hydraulic
    time period. Consecutive step in ENrunH - ENnextH loop.

    """
    deltat = ctypes.c_long()
    ierr = _lib.ENnextH(ctypes.byref(deltat))
    if ierr:
        raise ENtoolkitError(ierr)
    return deltat.value


def ENcloseH():
    """Closes the hydraulic analysis system, freeing all allocated memory.
    """
    ierr = _lib.ENcloseH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsolveQ():
    """Runs a complete water quality simulation with results at uniform
    reporting intervals written to EPANET's binary Output file.
    """
    ierr = _lib.ENsolveQ()
    if ierr:
        raise ENtoolkitError(ierr)


def ENopenQ():
    """Opens the water quality analysis system.
    """
    ierr = _lib.ENopenQ()
    if ierr:
        raise ENtoolkitError(ierr)


def ENinitQ(flag=None):
    """Initializes water quality and the simulation clock time prior to running
    a water quality analysis.

    Arguments
    ---------

    flag: flag indicating if analysis results should be saved to EPANET's binary
    output file at uniform reporting periods.

    flag  EN_NOSAVE | EN_SAVE
    """
    ierr = _lib.ENinitQ(flag)
    if ierr:
        raise ENtoolkitError(ierr)


def ENrunQ():
    """Return the current simulation clock time t.

    Makes available the hydraulic and water quality results that occur at the
    start of the next time period of a water quality analysis, where the start
    of the period is returned in t
    First step in ENrunQ - ENnextQ and ENrunQ - ENstepQ loop.
    """
    _t = ctypes.c_long()
    ierr = _lib.ENrunQ(ctypes.byref(_t))
    if ierr >= 100:
        raise ENtoolkitError(ierr)
    return _t.value

def ENnextQ():
    """Return the time (in seconds) until next hydraulic event occurs or 0 if
    at the end of the simulation period.

    Advances the water quality simulation to the start of the next hydraulic
    time period. Consecutive step in ENrunQ - ENnextQ loop.
    """
    _deltat = ctypes.c_long()
    ierr = _lib.ENnextQ(ctypes.byref(_deltat))
    if ierr:
        raise ENtoolkitError(ierr)
    return _deltat.value


def ENstepQ():
    """Return the time (in seconds) remaining in the overall simulation duration.

    Advances the water quality simulation one water quality time step. The time
    remaining in the overall simulation is returned. Consecutive step in ENrunQ
    - ENstepQ loop
    """
    _tleft = ctypes.c_long()
    ierr = _lib.ENnextQ(ctypes.byref(_tleft))
    if ierr:
        raise ENtoolkitError(ierr)
    return _tleft.value


def ENcloseQ():
    """Closes the water quality analysis system, freeing all allocated memory.
    """
    ierr = _lib.ENcloseQ()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsaveH():
    """Transfers results of a hydraulic simulation from the binary Hydraulics
    file to the binary output file, where results are only reported at uniform
    reporting intervals.
    """
    ierr = _lib.ENsaveH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsaveinpfile(fname):
    """Writes all current network input data to a file using the format of an
    EPANET input file.

    Arguments
    ---------
    fname: name of the file where data is saved
    """
    ierr = _lib.ENsaveinpfile(ctypes.c_char_p(fname.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENreport():
    """Writes a formatted text report on simulation results to the Report file.
    """
    ierr = _lib.ENreport()
    if ierr:
        raise ENtoolkitError(ierr)


def ENresetreport():
    """Clears any report formatting commands

    that either appeared in the [REPORT] section of the EPANET Input file or
    were issued with the ENsetreport function"""
    ierr = _lib.ENresetreport()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetreport(command):
    """Issues a report formatting command.

    Arguments
    ---------
    command: text of a report formatting command

    Formatting commands are the same as used in the [REPORT] section of the
    EPANET Input file.
    """
    ierr = _lib.ENsetreport(ctypes.c_char_p(command.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetstatusreport(statuslevel):
    """Sets the level of hydraulic status reporting.

   Arguments
   ---------
    statuslevel:  level of status reporting
                  0 - no status reporting
                  1 - normal reporting
                  2 - full status reporting
    """
    ierr = _lib.ENsetstatusreport(ctypes.c_int(statuslevel))
    if ierr:
        raise ENtoolkitError(ierr)


def ENgeterror(errcode):
    """Return the text of the message associated with a particular error or
    warning code.

    Arguments
    ---------
    errcode: error or warning code

    Error ranges:
        from   1 to   6 warning
        from 101 to 120 system error
        from 200 to 251 input error
        from 301 to 309 file error
    """
    _errmsg = ctypes.create_string_buffer(ERR_MAX_CHAR)
    _lib.ENgeterror(errcode, ctypes.byref(_errmsg), ERR_MAX_CHAR)
    return _errmsg.value.decode()


class ENtoolkitError(Exception):
    """Toolkit Error class."""
    def __init__(self, ierr):
        self.warning = ierr < 100
        self.args = (ierr,)
        self.message = ENgeterror(ierr)
        if self.message == '' and ierr:
            self.message = 'ENtoolkit Undocumented Error ' + str(ierr)
            self.message += ': look at text.h in epanet sources'

    def __str__(self):
        return self.message


EN_ELEVATION     = 0      # Node parameters
EN_BASEDEMAND    = 1
EN_PATTERN       = 2
EN_EMITTER       = 3
EN_INITQUAL      = 4
EN_SOURCEQUAL    = 5
EN_SOURCEPAT     = 6
EN_SOURCETYPE    = 7
EN_TANKLEVEL     = 8
EN_DEMAND        = 9
EN_HEAD          = 10
EN_PRESSURE      = 11
EN_QUALITY       = 12
EN_SOURCEMASS    = 13
EN_INITVOLUME    = 14
EN_MIXMODEL      = 15
EN_MIXZONEVOL    = 16

EN_TANKDIAM      = 17
EN_MINVOLUME     = 18
EN_VOLCURVE      = 19
EN_MINLEVEL      = 20
EN_MAXLEVEL      = 21
EN_MIXFRACTION   = 22
EN_TANK_KBULK    = 23

EN_DIAMETER      = 0      # Link parameters
EN_LENGTH        = 1
EN_ROUGHNESS     = 2
EN_MINORLOSS     = 3
EN_INITSTATUS    = 4
EN_INITSETTING   = 5
EN_KBULK         = 6
EN_KWALL         = 7
EN_FLOW          = 8
EN_VELOCITY      = 9
EN_HEADLOSS      = 10
EN_STATUS        = 11
EN_SETTING       = 12
EN_ENERGY        = 13

EN_DURATION      = 0      # Time parameters
EN_HYDSTEP       = 1
EN_QUALSTEP      = 2
EN_PATTERNSTEP   = 3
EN_PATTERNSTART  = 4
EN_REPORTSTEP    = 5
EN_REPORTSTART   = 6
EN_RULESTEP      = 7
EN_STATISTIC     = 8
EN_PERIODS       = 9

EN_NODECOUNT     = 0      # Component counts
EN_TANKCOUNT     = 1
EN_LINKCOUNT     = 2
EN_PATCOUNT      = 3
EN_CURVECOUNT    = 4
EN_CONTROLCOUNT  = 5

EN_JUNCTION      = 0      # Node types
EN_RESERVOIR     = 1
EN_TANK          = 2

EN_CVPIPE        = 0      # Link types
EN_PIPE          = 1
EN_PUMP          = 2
EN_PRV           = 3
EN_PSV           = 4
EN_PBV           = 5
EN_FCV           = 6
EN_TCV           = 7
EN_GPV           = 8

EN_NONE          = 0      # Quality analysis types
EN_CHEM          = 1
EN_AGE           = 2
EN_TRACE         = 3

EN_CONCEN        = 0      # Source quality types
EN_MASS          = 1
EN_SETPOINT      = 2
EN_FLOWPACED     = 3

EN_CFS           = 0      # Flow units types
EN_GPM           = 1
EN_MGD           = 2
EN_IMGD          = 3
EN_AFD           = 4
EN_LPS           = 5
EN_LPM           = 6
EN_MLD           = 7
EN_CMH           = 8
EN_CMD           = 9

EN_TRIALS        = 0      # Misc. options
EN_ACCURACY      = 1
EN_TOLERANCE     = 2
EN_EMITEXPON     = 3
EN_DEMANDMULT    = 4

EN_LOWLEVEL      = 0      # Control types
EN_HILEVEL       = 1
EN_TIMER         = 2
EN_TIMEOFDAY     = 3

EN_AVERAGE       = 1      # Time statistic types
EN_MINIMUM       = 2
EN_MAXIMUM       = 3
EN_RANGE         = 4

EN_MIX1          = 0      # Tank mixing models
EN_MIX2          = 1
EN_FIFO          = 2
EN_LIFO          = 3

EN_NOSAVE        = 0      # Save-results-to-file flag
EN_SAVE          = 1
EN_INITFLOW      = 10     # Re-initialize flow flag

EN_NO_REPORT     = 0      # no status reporting
EN_NORMAL_REPORT = 1      # normal reporting
EN_FULL_REPORT   = 2      # full status reportin
