<p align="center"><img src="wnt/resources/wnt.png" width="345" height="293" title="WNT Logo"></p>

# Water Network Tools (WNT)
A set of processes for modelling water networks. Starting from scratch or expanding an existing network, WNT can import and export EPANET models, scenario files and optimization inputs.

## Recipes
### Build
- Build EPANET-style node and link layers from CAD/GIS lines.

### Demand
- Assign demand.
- Connect entities by distance.
- Update assignment.

### Export
- Build an EPANET model file from network layers with two workflows:
  - A: add nodes and links to an existing `.inp` model.
  - B: create a new `.inp` model from a minimal internal EPANET template, selecting EPANET `2.00.12` or `2.2+` and the flow units.
- Build an EPANET demand scenario file (`.scn`) from mandatory demand fields in the node layer.
- Build an EPANET pipe properties scenario file (`.scn`) with `[DIAMETERS]` and `[ROUGHNESS]` sections from pipe diameter and roughness fields.
- Build a PPNO (`Pressurized Pipe Network Optimizer`) data file (`.ext`) from network layers, an EPANET `.inp` model and a pipe catalog `.cat` file. PPNO is a command-line optimizer that uses EPANET simulations, minimum pressure constraints, pipe groups and optional global algorithms (`DE`, `DA`, `NSGA2`, `MOEAD`, `MACO`, `PSO`). See https://github.com/andresgciamtez/ppno.

### Fire
- Generate hydrant pair connection lines. Pairs farther apart than the maximum separation are not generated.

### Graph
- Classify branched and meshed zones.
- Export graph network to TGF.
- Get node degrees.
- Validate network.

### Import
- Configure the EPANET toolkit library.
- Import an EPANET file as node and link layers.
- Import network from LandXML.
- Import EPANET simulation results.

### Modify
- Add elevation to nodes from a DEM.
- Add elevation to nodes from a TIN surface (LandXML v1.2).
- Split polylines at points to correct models that ignore connection points.
- Merge networks.

Andres Garcia Martinez (ppnoptimizer@gmail.com)

===

# Water Network Tools (WNT)
Un conjunto de procesos para el modelado de redes de agua. Partiendo desde cero o ampliando una red existente, WNT permite importar y exportar modelos EPANET, archivos de escenario y datos de optimización.

## Recetas

### Modelar
- Genera capas de nodos y links con estructura EPANET a partir de líneas CAD/GIS.

### Demanda
- Asignar demanda.
- Actualizar demanda.
- Conectar entidades por proximidad.

### Exportar
- Genera un modelo EPANET desde las capas de red con dos flujos de trabajo:
  - A: añadir nodos y links a un modelo `.inp` existente.
  - B: crear un modelo `.inp` nuevo desde una plantilla mínima interna de EPANET, seleccionando EPANET `2.00.12` o `2.2+` y las unidades de caudal.
- Genera un archivo de escenario de demandas de EPANET (`.scn`) a partir de campos obligatorios de demanda en la capa de nodos.
- Genera un archivo de escenario de propiedades de tuberías de EPANET (`.scn`) con secciones `[DIAMETERS]` y `[ROUGHNESS]` desde campos de diámetro y rugosidad.
- Genera un archivo de datos PPNO (`.ext`) desde las capas de red, un modelo EPANET `.inp` y un catálogo de tuberías `.cat`. PPNO (`Pressurized Pipe Network Optimizer`) es un optimizador de línea de comandos que usa simulaciones EPANET, restricciones de presión mínima, grupos de tubería y algoritmos globales opcionales (`DE`, `DA`, `NSGA2`, `MOEAD`, `MACO`, `PSO`). Consulta https://github.com/andresgciamtez/ppno.

### Fuego
- Genera líneas de pares de hidrantes. No se generan pares separados por una distancia mayor que la separación máxima.

### Grafo
- Clasifica la red en zonas malladas y ramificadas identificando subredes.
- Exporta el grafo de la red a TGF.
- Calcula el grado de los nodos de la red.
- Verifica la red.

### Importar
- Configura el acceso a la biblioteca de EPANET.
- Importa una red EPANET como capas de nodos y links.
- Importa una red desde LandXML.
- Importa resultados de simulación EPANET.

### Modificar
- Añade elevación a nodos desde un modelo digital de elevaciones.
- Añade elevación a nodos desde una superficie TIN (LandXML v1.2).
- Parte líneas en puntos especificados para añadir uniones.
- Fusiona dos redes.

Andres Garcia Martinez (ppnoptimizer@gmail.com)
