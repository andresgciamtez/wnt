<p align="center"><img src="/wnt.png" width="345" height="293" title="WNT Logo"></p>

# Water Network Tools (WNT)
A set of processes for modelling water networks. Starting from scratch or expanding an existing network, it is possible to import and export models, scenarios and other files for network analysis or optimization.

## Recipes
### Build
- Build a network, topology and geometry, from lines:http://y2u.be/Mjtwar1H1jA
### Demand
- Assignate demand
- Connect entities by distance
- Update assignment
### Export
- Build an epanet model file from network: http://y2u.be/L7Kp5l67kOc
- Build an epanet scenario file containing demands: http://y2u.be/FOxZgZUgjq4
- Build an epanet scenario file containing pipe properties (diameter and roughness): http://y2u.be/wvbyWapAu2I
- Build a pressurized pipe network optimizer (ppno) data file: http://y2u.be/S9445JLldRE
## Fire
- Combine pairs of hydrants
### Graph
- Classify (branched and meshed zones)
- Export graph network to TGF: http://y2u.be/gMYElJa37bg
- Get node degrees
- Validate network
### Import
- Configure epanet lib
- Import an epanet file (nodes and link): http://y2u.be/fxhAPB4ZIyg
- Import network from LandXML
- Import results from epanet
### Modify
- Add elevation to nodes from a DEM: http://y2u.be/IfDK1yyEPIE
- Add elevation to nodes from a TIN (LandXML v1.2)
- Split polylines at points, correcting models that ignore connection points (T, X, n-junctions): http://y2u.be/yJ_75TPSk6o
- Merge networks

Andrés García Martínez (ppnoptimizer@gmail.com)

===

# Water Network Tools (WNT)
Un conjunto de procesos para el modelado de redes de agua. Partiendo desde cero o ampliando una red existente, permite importar y exportar modelos, escenarios y otros archivos con la finalidad de analizar u optimizar una red.

## Recetas

### Modelar
- Genera un red, topología y geometría, desde líneas cad o shp: http://y2u.be/Mjtwar1H1jA
### Demanda
- Asignar demanda
- Actualizar demanda
- Conectar entidades por proximidad
### Exportar
- Genera un modelo epanet (o amplía uno existente) desde la red (nodos y líneas) y una plantilla: http://y2u.be/L7Kp5l67kOc
- Genera un escenario de demandas para epanet: http://y2u.be/FOxZgZUgjq4
- Gnera un escenario con las propiedades de las tuberías (díametro y rugosidad) para epanet: http://y2u.be/wvbyWapAu2I
- Genera un archivo de datos para ppno (pressurized pipe network optimizer): http://y2u.be/S9445JLldRE
### Fuego
- Genera combinaciones de pares de hidrantes no separados más de una distancia prefijada
### Grafo
- Clasifica la red en zonas malladas y ramificadas identificando las subredes
- Exporta el grafo de la red a TGF: http://y2u.be/gMYElJa37bg
- Cálcular el grado de los nodos de la red
- Verifica la red
### Importar
- Configura el acceso a la biblioteca de epanet
- Importar un red de epanet (nodos y líneas): http://y2u.be/fxhAPB4ZIyg
- Importar red desde LandXML
- Importa los resultados del cálculo
### Modificar
- Añadir elevación a nodos desde un modelo digital de elevaciones: http://y2u.be/IfDK1yyEPIE
- Añadir elevación a nodos desde una superficie TIN (LandXML v1.2)
- Partir línea en puntos especificados (para añadir uniones): http://y2u.be/yJ_75TPSk6o
- Fusiona dos redes

Andrés García Martínez (ppnoptimizer@gmail.com)
