# Water Network Tools (WNT) - AI Coding Assistant Instructions

## Project Overview
WNT is a QGIS plugin providing processing algorithms for water network modeling. It enables importing/exporting EPANET models, building networks from GIS data, assigning demands, and analyzing network topology. The plugin integrates with EPANET hydraulic simulation toolkit via ctypes.

## Architecture
- **Plugin Structure**: Main plugin class loads a `WaterNetworkToolsProvider` that registers ~20 processing algorithms
- **Algorithm Pattern**: Each tool inherits from `QgsProcessingAlgorithm` with:
  - `initAlgorithm()`: Define input/output parameters
  - `processAlgorithm()`: Core logic using QGIS API and custom utilities
- **Utilities**: Modular `utils_*.py` files handle core functionality:
  - `utils_core.py`: Geometry operations, network building, ID formatting
  - `utils_parser.py`: EPANET file parsing with `[SECTION]` headers
  - `utils_graph.py`: Network topology analysis
  - `utils_landxml.py`: LandXML format handling
  - `utils_tin.py`: TIN surface operations
  - `utils_split.py`: Geometry splitting utilities

## Key Patterns & Conventions

### Algorithm Implementation
```python
class ExampleAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        # Add parameters using self.addParameter(QgsProcessingParameter*)
        self.addParameter(QgsProcessingParameterFeatureSource(INPUT, tr('Input layer')))
        self.addParameter(QgsProcessingParameterFeatureSink(OUTPUT, tr('Output layer')))
    
    def processAlgorithm(self, parameters, context, feedback):
        # Extract parameters
        source = self.parameterAsSource(parameters, self.INPUT, context)
        # Use feedback for progress/info: feedback.pushInfo('Processing...')
        # Core logic using utils functions
        result = tools.some_function(data)
        # Create output sink and add features
        sink = self.parameterAsSink(parameters, self.OUTPUT, context, fields, geom_type, crs)
        return {self.OUTPUT: sink_id}
```

### Network Data Model
- **Nodes**: Fields `id` (string), `type` (JUNCTION/RESERVOIR/TANK), `elevation` (double)
- **Links**: Fields `id` (string), `start` (node_id), `end` (node_id), `type` (PIPE/PUMP/etc.), `length` (double)
- **ID Formatting**: Use `tools.format_id(number, mask)` with masks like `'P-$$-S'` for `'P-01-S'`

### EPANET Integration
- Configure library path in `toolkit.ini` [EPANET] lib = /path/to/epanet2.dll
- Use `toolkit.py` for simulation results via ctypes
- File formats: .inp (model), .rpt (results), .scn (scenarios)

### Error Handling & Logging
- Use `feedback.reportError()` for errors, `feedback.pushInfo()` for info
- Validate geometries: Check for MultiGeometry, looped lines, CRS
- Follow EPANET conventions: No loops, valid node/link types

## Development Workflow

### Setup
1. Install QGIS 3.0+ with Python support
2. Configure EPANET toolkit path in `toolkit.ini`
3. Run tests: `python -m unittest test.test_*`

### Building & Deployment
- **Plugin Package**: Use pb_tool with `pb_tool.cfg` configuration
- **Translations**: Update `.ts` files, compile to `.qm` with scripts
- **Documentation**: Sphinx in `help/` directory, build with `make html`
- **Upload**: Use `plugin_upload.py` to QGIS plugin repository

### Testing
- Unit tests in `test/` directory using unittest
- Mock QGIS interface with `qgis_interface.py`
- Test data: Sample rasters, geometries in test directory

## Common Tasks

### Adding New Algorithm
1. Create `wnt_new_tool.py` inheriting from `QgsProcessingAlgorithm`
2. Implement required methods: `name()`, `displayName()`, `group()`, `initAlgorithm()`, `processAlgorithm()`
3. Add to `wnt_provider.py` loadAlgorithms()
4. Update `pb_tool.cfg` python_files list
5. Add help strings in English/Spanish

### Modifying Network Logic
- Core functions in `utils_core.py`: `net_from_linestrings()`, `format_id()`, geometric ops
- Graph operations in `utils_graph.py`: connectivity, node degrees
- Preserve existing field naming conventions

### EPANET File Handling
- Use `HeadedText` class for parsing/writing sectioned files
- Sections like `[JUNCTIONS]`, `[PIPES]`, `[DEMANDS]`
- Handle encoding: `latin-1` for EPANET files

## Dependencies & Environment
- **Runtime**: QGIS 3.0+, EPANET 2.x toolkit library
- **Development**: Python 3.6+, ctypes for EPANET binding
- **Build**: pb_tool for packaging, Sphinx for docs
- **Linting**: pylint with custom config disabling C0103, locally-disabled

Remember: All algorithms must handle QGIS feedback/progress, validate inputs, and maintain network topology integrity.