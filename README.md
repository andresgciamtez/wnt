<p align="center"><img src="wnt/resources/wnt.png" width="345" height="293" title="WNT Logo"></p>

# Water Network Tools (WNT)

Water Network Tools is a QGIS Processing plugin for creating, editing, validating, importing and exporting pressurized water network data. It works with WNT node/link layers, EPANET `.inp` files, EPANET scenario files, WNT XML, LandXML pipe networks, LandXML TIN surfaces and pipe-sizing inputs.

## Recipes

### Build

- Build EPANET-style node and link layers from CAD/GIS lines.
- Optionally add node elevations from line Z values, a DEM raster or one selected LandXML TIN surface.
- Optionally add node degree and link topology/zone fields while building the network.

### Demand

- Assign demand from source features to network nodes.
- Connect entities by nearest distance.
- Update demand assignments after editing assignment lines.

### Export

- Build an EPANET model file (`.inp`) from network layers.
  - Output mode `Add links and nodes to existing EPANET model` merges the selected network into an existing `.inp` model.
  - Output mode `Create EPANET model from scratch` creates a new `.inp` model from the internal EPANET template.
  - The final graph is validated before the file is written.
- Build EPANET scenario files (`.scn`) for demands, pipe diameters and pipe roughness.
- Build WNT Network XML or LandXML 1.2 pipe-network files from WNT node and link layers.
- Build pipesizing data files (`.pro`) with `[SETTINGS]`, `[PRESSURES]`, `[FIRE_SCENARIOS]` and `[PIPES]` sections.
  - Peak and fire demand factors are configured in the Processing form.
  - Required peak-flow and fire-flow pressures are read from node fields.
  - Fire scenarios can be written from a hydrant pairs layer.
- Build PPNO (`Pressurized Pipe Network Optimizer`) data files (`.ext`) from network layers, an EPANET `.inp` model and a pipe catalog `.cat` file. See https://github.com/andresgciamtez/ppno.

### Fire Scenarios

- Generate hydrant pairs/calculation scenarios from a hydrant layer.
- Pairs farther apart than the maximum separation are not generated.
- The generated layer can be used by the pipesizing `.pro` exporter as fire scenarios.

### Graph

- Classify links as branched or meshed and assign a globally unique `zone`.
- Calculate node degrees.
- Export the network graph to TGF.
- Validate the graph for orphan nodes, duplicate nodes, duplicate links, links with undefined endpoints and loops.

### Import

- Configure the EPANET toolkit library path.
- Import EPANET `.inp` files as node and link layers.
- Import hydraulic results, quality results or both from EPANET simulations.
- Import WNT Network XML or LandXML 1.2 pipe networks as node and link layers.

### Modify

- Add or update node elevations from a DEM raster.
- Add or update node elevations from one selected LandXML TIN surface.
- Split lines at points.
- Merge two networks; the final graph is validated before output layers are created.

Andres Garcia Martinez (ppnoptimizer@gmail.com)

===

# Water Network Tools (WNT)

Water Network Tools es un plugin de QGIS Processing para crear, editar, validar, importar y exportar datos de redes de agua a presión. Trabaja con capas WNT de nodos/links, archivos EPANET `.inp`, escenarios EPANET, XML de WNT, redes LandXML, superficies TIN LandXML y datos para dimensionamiento de tuberías.

## Recetas

### Modelar

- Genera capas de nodos y links con estructura EPANET a partir de líneas CAD/GIS.
- Permite añadir elevaciones de nodo desde valores Z de las líneas, un ráster MDE o una superficie TIN LandXML seleccionada.
- Permite añadir el grado de los nodos y los campos de topología/zone de los links durante la creación de la red.

### Demanda

- Asigna demanda desde entidades de origen a nodos de la red.
- Conecta entidades por distancia mínima.
- Actualiza asignaciones de demanda después de editar las líneas de asignación.

### Exportar

- Genera un archivo de modelo EPANET (`.inp`) desde capas de red.
  - El modo de salida `Add links and nodes to existing EPANET model` fusiona la red seleccionada con un modelo `.inp` existente.
  - El modo de salida `Create EPANET model from scratch` crea un modelo `.inp` nuevo desde la plantilla interna de EPANET.
  - El grafo final se valida antes de escribir el archivo.
- Genera archivos de escenario EPANET (`.scn`) de demandas, diámetros y rugosidades.
- Genera archivos WNT Network XML o redes de tuberías LandXML 1.2 desde capas WNT de nodos y links.
- Genera archivos de datos pipesizing (`.pro`) con secciones `[SETTINGS]`, `[PRESSURES]`, `[FIRE_SCENARIOS]` y `[PIPES]`.
  - Los factores punta y de incendio se configuran en el formulario de Processing.
  - Las presiones mínimas para caudal punta e incendio se leen desde campos de la capa de nodos.
  - Los escenarios de incendio pueden escribirse desde una capa de pares de hidrantes.
- Genera archivos de datos PPNO (`.ext`) desde capas de red, un modelo EPANET `.inp` y un catálogo de tuberías `.cat`. Consulta https://github.com/andresgciamtez/ppno.

### Escenarios de incendio

- Genera pares de hidrantes/escenarios de cálculo desde una capa de hidrantes.
- No se generan pares separados por una distancia mayor que la separación máxima.
- La capa generada puede usarse como entrada de escenarios de incendio en el exportador pipesizing `.pro`.

### Grafo

- Clasifica links como ramificados o mallados y asigna un `zone` globalmente único.
- Calcula el grado de los nodos.
- Exporta el grafo de la red a TGF.
- Valida el grafo para detectar nodos huérfanos, nodos duplicados, links duplicados, links con extremos no definidos y bucles.

### Importar

- Configura la ruta de la biblioteca del toolkit de EPANET.
- Importa archivos EPANET `.inp` como capas de nodos y links.
- Importa resultados hidráulicos, resultados de calidad o ambos desde simulaciones EPANET.
- Importa WNT Network XML o redes de tuberías LandXML 1.2 como capas de nodos y links.

### Modificar

- Añade o actualiza elevaciones de nodos desde un ráster MDE.
- Añade o actualiza elevaciones de nodos desde una superficie TIN LandXML seleccionada.
- Divide líneas en puntos.
- Fusiona dos redes; el grafo final se valida antes de crear las capas de salida.

Andres Garcia Martinez (ppnoptimizer@gmail.com)
