"""Small EPANET toolkit facade used by Processing algorithms."""

import ctypes
import os
import platform
import tempfile
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from time import gmtime, strftime


@dataclass(frozen=True)
class EpanetConstants:
    """Version-aware EPANET API constants.

    The toolkit exposes these values as C macros/enums, not exported runtime
    symbols. Resolve them once from the toolkit version instead of scattering
    numeric literals through the wrapper.
    """

    node_count: int
    link_count: int
    demand: int
    head: int
    pressure: int
    flow: int
    velocity: int
    headloss: int
    status: int
    setting: int
    energy: int
    no_save: int
    max_label_len: int


def constants_for_version(version):
    """Return the EPANET constants profile for a toolkit version code."""
    value = int(version or 0)
    max_label_len = 31 if value >= 20200 else 15
    return EpanetConstants(
        node_count=0,
        link_count=2,
        demand=9,
        head=10,
        pressure=11,
        flow=8,
        velocity=9,
        headloss=10,
        status=11,
        setting=12,
        energy=13,
        no_save=0,
        max_label_len=max_label_len,
    )


class EpanetError(Exception):
    """Raised when the EPANET toolkit reports an error."""

    def __init__(self, code, message=None):
        self.code = int(code)
        self.message = message or f"EPANET toolkit error {self.code}"
        super().__init__(self.message)


class EpanetConfigurationError(Exception):
    """Raised when the toolkit library is missing or cannot be loaded."""


@dataclass(frozen=True)
class ToolkitInfo:
    """Information reported for a loaded EPANET toolkit library."""

    library_path: str
    platform: str
    architecture: str
    version: str
    api: str


@dataclass(frozen=True)
class EpanetResults:
    """Hydraulic time-series results read from an EPANET input file."""

    node_rows: list
    link_rows: list
    step_count: int
    node_count: int
    link_count: int


def toolkit_config_path(base_path=None):
    """Return the user-writable toolkit.ini path."""
    if base_path is not None:
        root = Path(base_path)
    else:
        settings_path = None
        try:
            from qgis.core import QgsApplication
            settings_path = QgsApplication.qgisSettingsDirPath()
        except (ImportError, AttributeError, RuntimeError):
            settings_path = None
        root = (Path(settings_path) / "wnt") if settings_path else (Path.home() / ".wnt")
    root.mkdir(parents=True, exist_ok=True)
    return root / "toolkit.ini"


def read_toolkit_library_path(config_path=None):
    """Read the configured EPANET toolkit library path."""
    path = Path(config_path) if config_path is not None else toolkit_config_path()
    config = ConfigParser()
    config.read(path)
    try:
        lib_path = config["EPANET"]["lib"].strip()
    except KeyError as exc:
        raise EpanetConfigurationError("Configure EPANET toolkit library") from exc
    if not lib_path:
        raise EpanetConfigurationError("Configure EPANET toolkit library")
    return lib_path


def write_toolkit_library_path(lib_path, config_path=None):
    """Persist the configured EPANET toolkit library path."""
    path = Path(config_path) if config_path is not None else toolkit_config_path()
    config = ConfigParser()
    config.read(path)
    if not config.has_section("EPANET"):
        config.add_section("EPANET")
    config["EPANET"]["lib"] = str(lib_path)
    with open(path, "w", encoding="utf-8") as config_file:
        config.write(config_file)
    return path


def format_toolkit_version(version):
    """Convert an EPANET integer version code into a readable string."""
    if version is None:
        return "unknown"
    value = int(version)
    major = value // 10000
    minor = (value % 10000) // 100
    patch = value % 100
    if major:
        return f"{major}.{minor}.{patch}"
    return str(value)


def _set_signature(function, argtypes):
    try:
        function.argtypes = argtypes
        function.restype = ctypes.c_int
    except (AttributeError, TypeError):
        pass


def _load_library(lib_path):
    system = platform.system().lower()
    if system == "windows":
        loader = getattr(ctypes, "WinDLL", None)
        if loader is not None:
            return loader(str(lib_path))
        return ctypes.windll.LoadLibrary(str(lib_path))
    return ctypes.CDLL(str(lib_path))


class EpanetToolkit:
    """Pythonic wrapper around the EPANET global toolkit API.

    The implementation follows the same ctypes style as entoolkit's legacy
    wrapper, but receives the library path from WNT configuration instead of
    bundling a platform-specific binary.
    """

    REQUIRED_SYMBOLS = (
        "ENopen",
        "ENclose",
        "ENgetcount",
        "ENopenH",
        "ENinitH",
        "ENrunH",
        "ENnextH",
        "ENgetnodeid",
        "ENgetnodevalue",
        "ENgetlinkid",
        "ENgetlinkvalue",
    )

    def __init__(self, library, library_path):
        self._lib = library
        self.library_path = str(library_path)
        self._project_open = False
        self._configure_signatures()
        self._check_required_symbols()
        self._version_code = self._read_version_code()
        self.constants = constants_for_version(self._version_code)

    @classmethod
    def from_library_path(cls, lib_path):
        try:
            library = _load_library(lib_path)
        except OSError as exc:
            raise EpanetConfigurationError(str(exc)) from exc
        return cls(library, lib_path)

    @classmethod
    def from_config(cls, config_path=None):
        return cls.from_library_path(read_toolkit_library_path(config_path))

    @property
    def platform(self):
        return platform.system() or os.name

    @property
    def architecture(self):
        return platform.machine() or "unknown"

    @property
    def api(self):
        if all(hasattr(self._lib, name) for name in ("EN_createproject", "EN_deleteproject")):
            return "project-handle and legacy"
        return "legacy"

    @property
    def version(self):
        return format_toolkit_version(self._version_code)

    def info(self):
        """Return platform and toolkit metadata."""
        return ToolkitInfo(
            library_path=self.library_path,
            platform=self.platform,
            architecture=self.architecture,
            version=self.version,
            api=self.api,
        )

    def check_available(self):
        """Call a lightweight toolkit function to verify the library works."""
        self.info()
        return True

    def read_hydraulic_results(self, inp_file):
        """Run hydraulics and return node/link results for each time step."""
        with tempfile.NamedTemporaryFile(suffix=".rpt", delete=False) as report:
            report_file = report.name
        node_rows = []
        link_rows = []
        step_count = 0
        try:
            self.open(inp_file, report_file)
            node_count = self.getcount(self.constants.node_count)
            link_count = self.getcount(self.constants.link_count)
            self.open_hydraulics()
            self.init_hydraulics(self.constants.no_save)
            while True:
                step_count += 1
                current_time = strftime("%H:%M:%S", gmtime(self.run_hydraulics()))
                for index in range(1, node_count + 1):
                    node_rows.append(
                        [
                            current_time,
                            self.getnodeid(index),
                            self.getnodevalue(index, self.constants.demand),
                            self.getnodevalue(index, self.constants.head),
                            self.getnodevalue(index, self.constants.pressure),
                        ]
                    )
                for index in range(1, link_count + 1):
                    status = self.getlinkvalue(index, self.constants.status)
                    link_rows.append(
                        [
                            current_time,
                            self.getlinkid(index),
                            self.getlinkvalue(index, self.constants.flow),
                            self.getlinkvalue(index, self.constants.velocity),
                            self.getlinkvalue(index, self.constants.headloss),
                            "OPEN" if status else "CLOSED",
                            self.getlinkvalue(index, self.constants.setting),
                            self.getlinkvalue(index, self.constants.energy),
                        ]
                    )
                if self.next_hydraulics() == 0:
                    break
        finally:
            if self._project_open:
                self.close()
            try:
                Path(report_file).unlink(missing_ok=True)
            except OSError:
                pass
        return EpanetResults(node_rows, link_rows, step_count, node_count, link_count)

    def open(self, inp_file, report_file):
        inp = ctypes.c_char_p(str(inp_file).encode())
        rpt = ctypes.c_char_p(str(report_file).encode())
        bin_file = ctypes.c_char_p(b"")
        try:
            err = self._lib.ENopen(inp, rpt, bin_file)
        except TypeError:
            err = self._lib.ENopen(inp, rpt)
        self._check(err)
        self._project_open = True

    def close(self):
        self._check(self._lib.ENclose())
        self._project_open = False

    def getcount(self, code):
        count = ctypes.c_int()
        self._check(self._lib.ENgetcount(code, ctypes.byref(count)))
        return count.value

    def open_hydraulics(self):
        self._check(self._lib.ENopenH())

    def init_hydraulics(self, flag):
        self._check(self._lib.ENinitH(ctypes.c_int(flag)))

    def run_hydraulics(self):
        current_time = ctypes.c_long()
        self._check(self._lib.ENrunH(ctypes.byref(current_time)))
        return current_time.value

    def next_hydraulics(self):
        next_time = ctypes.c_long()
        self._check(self._lib.ENnextH(ctypes.byref(next_time)))
        return next_time.value

    def getnodeid(self, index):
        node_id = ctypes.create_string_buffer(self.constants.max_label_len + 1)
        self._check(self._lib.ENgetnodeid(index, node_id))
        return node_id.value.decode("utf-8")

    def getnodevalue(self, index, parameter):
        value = ctypes.c_float()
        self._check(self._lib.ENgetnodevalue(index, parameter, ctypes.byref(value)))
        return float(value.value)

    def getlinkid(self, index):
        link_id = ctypes.create_string_buffer(self.constants.max_label_len + 1)
        self._check(self._lib.ENgetlinkid(index, link_id))
        return link_id.value.decode("utf-8")

    def getlinkvalue(self, index, parameter):
        value = ctypes.c_float()
        self._check(self._lib.ENgetlinkvalue(index, parameter, ctypes.byref(value)))
        return float(value.value)

    def _read_version_code(self):
        if not hasattr(self._lib, "ENgetversion"):
            return None
        version = ctypes.c_int()
        self._check(self._lib.ENgetversion(ctypes.byref(version)))
        return version.value

    def _check(self, code):
        if code:
            raise EpanetError(code, self.geterror(code))

    def geterror(self, code):
        if not hasattr(self._lib, "ENgeterror"):
            return f"EPANET toolkit error {int(code)}"
        message = ctypes.create_string_buffer(256)
        try:
            self._lib.ENgeterror(int(code), message, 255)
        except TypeError:
            return f"EPANET toolkit error {int(code)}"
        text = message.value.decode("utf-8")
        return text or f"EPANET toolkit error {int(code)}"

    def _check_required_symbols(self):
        missing = [name for name in self.REQUIRED_SYMBOLS if not hasattr(self._lib, name)]
        if missing:
            raise EpanetConfigurationError(
                "EPANET toolkit library is missing required functions: "
                + ", ".join(missing)
            )

    def _configure_signatures(self):
        p_char = ctypes.c_char_p
        p_int = ctypes.POINTER(ctypes.c_int)
        p_long = ctypes.POINTER(ctypes.c_long)
        p_float = ctypes.POINTER(ctypes.c_float)
        signatures = {
            "ENopen": [p_char, p_char, p_char],
            "ENclose": [],
            "ENgeterror": [ctypes.c_int, p_char, ctypes.c_int],
            "ENgetversion": [p_int],
            "ENgetcount": [ctypes.c_int, p_int],
            "ENopenH": [],
            "ENinitH": [ctypes.c_int],
            "ENrunH": [p_long],
            "ENnextH": [p_long],
            "ENgetnodeid": [ctypes.c_int, p_char],
            "ENgetnodevalue": [ctypes.c_int, ctypes.c_int, p_float],
            "ENgetlinkid": [ctypes.c_int, p_char],
            "ENgetlinkvalue": [ctypes.c_int, ctypes.c_int, p_float],
        }
        for name, argtypes in signatures.items():
            if hasattr(self._lib, name):
                _set_signature(getattr(self._lib, name), argtypes)
