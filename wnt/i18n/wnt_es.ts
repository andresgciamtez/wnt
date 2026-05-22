<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="es">
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_assign_demand.py" line="67"/>
        <source>&lt;p&gt;Assigns demand from a &lt;b&gt;source layer&lt;/b&gt; to a &lt;b&gt;target node layer&lt;/b&gt; using the nearest target feature.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Both input layers must contain an &lt;code&gt;id&lt;/code&gt; field.&lt;/li&gt;
&lt;li&gt;The selected source demand fields are copied and accumulated in the target layer.&lt;/li&gt;
&lt;li&gt;The output assignment layer stores the connection lines between source and target features.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Use &lt;b&gt;Update assignment&lt;/b&gt; after editing assignment lines.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Asigna demandas desde una &lt;b&gt;capa de origen&lt;/b&gt; a una &lt;b&gt;capa de nodos de destino&lt;/b&gt; usando la entidad de destino más cercana.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Ambas capas de entrada deben contener un campo &lt;code&gt;id&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Los campos de demanda seleccionados de la capa de origen se copian y acumulan en la capa de destino.&lt;/li&gt;
&lt;li&gt;La capa de asignaciones de salida almacena las líneas de conexión entre las entidades de origen y destino.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Usa &lt;b&gt;Update assignment&lt;/b&gt; después de editar las líneas de asignación.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_assign_demand.py" line="82"/>
        <source>Source layer</source>
        <translation type="unfinished">Capa de origen</translation>
    </message>
    <message>
        <location filename="../processes/wnt_assign_demand.py" line="89"/>
        <source>Source demand fields</source>
        <translation type="unfinished">Campos de demanda de origen</translation>
    </message>
    <message>
        <location filename="../processes/wnt_assign_demand.py" line="99"/>
        <source>Target layer</source>
        <translation type="unfinished">Capa de destino</translation>
    </message>
    <message>
        <location filename="../processes/wnt_assign_demand.py" line="108"/>
        <source>Assignment layer</source>
        <translation type="unfinished">Capa de asignaciones</translation>
    </message>
    <message>
        <location filename="../processes/wnt_assign_demand.py" line="114"/>
        <source>Target with demands layer</source>
        <translation type="unfinished">Capa de destino con demandas</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_classify.py" line="63"/>
        <source>&lt;p&gt;Classifies network links into branched and meshed areas.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Adds or updates &lt;code&gt;topology&lt;/code&gt;: &lt;code&gt;branched&lt;/code&gt; or &lt;code&gt;mesh&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Adds or updates &lt;code&gt;zones&lt;/code&gt;: subnetwork identifier.&lt;/li&gt;
&lt;li&gt;Can create a new output layer or update the input link layer.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Use this algorithm to support network sectorization.&lt;/p&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_classify.py" line="78"/>
        <source>Network links layer input</source>
        <translation type="unfinished">Capa de links de red de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_classify.py" line="85"/>
        <source>Output mode</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_classify.py" line="96"/>
        <source>Subnetwork link layer</source>
        <translation type="unfinished">Capa de links de subred</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_config_toolkit.py" line="60"/>
        <source>&lt;p&gt;Sets the path to the EPANET toolkit library.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The path is stored in &lt;code&gt;toolkit.ini&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Configure this before importing EPANET simulation results.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;EPANET toolkit libraries can be obtained from the EPA EPANET download page or from a compatible EPANET toolkit build.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Define la ruta de la biblioteca del toolkit de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;La ruta se guarda en &lt;code&gt;toolkit.ini&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Configúrala antes de importar resultados de simulaciones de EPANET.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Las bibliotecas del toolkit de EPANET pueden obtenerse desde la página de descargas de EPANET de la EPA o desde una compilación compatible del toolkit de EPANET.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_config_toolkit.py" line="73"/>
        <source>EPANET lib</source>
        <translation type="unfinished">Biblioteca EPANET</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_connect_by_distance.py" line="68"/>
        <source>&lt;p&gt;Connects features from a &lt;b&gt;source layer&lt;/b&gt; to a &lt;b&gt;target layer&lt;/b&gt; by minimum distance.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Both layers must contain an &lt;code&gt;id&lt;/code&gt; field.&lt;/li&gt;
&lt;li&gt;The maximum number of connections and maximum distance limit the generated links.&lt;/li&gt;
&lt;li&gt;The output is a line layer representing the connections.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Conecta entidades de una &lt;b&gt;capa de origen&lt;/b&gt; con una &lt;b&gt;capa de destino&lt;/b&gt; por distancia mínima.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Ambas capas deben contener un campo &lt;code&gt;id&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;El número máximo de conexiones y la distancia máxima limitan los links generados.&lt;/li&gt;
&lt;li&gt;La salida es una capa de links que representa las conexiones.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_connect_by_distance.py" line="82"/>
        <source>Source layer</source>
        <translation type="unfinished">Capa de origen</translation>
    </message>
    <message>
        <location filename="../processes/wnt_connect_by_distance.py" line="90"/>
        <source>Target layer</source>
        <translation type="unfinished">Capa de destino</translation>
    </message>
    <message>
        <location filename="../processes/wnt_connect_by_distance.py" line="98"/>
        <source>Max number of connections</source>
        <translation type="unfinished">Número máximo de conexiones</translation>
    </message>
    <message>
        <location filename="../processes/wnt_connect_by_distance.py" line="107"/>
        <source>Max distance</source>
        <translation type="unfinished">Distancia máxima</translation>
    </message>
    <message>
        <location filename="../processes/wnt_connect_by_distance.py" line="117"/>
        <source>Connection layer</source>
        <translation type="unfinished">Capa de conexiones</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_demand_to_epanet_scenario.py" line="55"/>
        <source>&lt;p&gt;Creates an EPANET demand scenario file.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Each demand category must be stored in a field of the node layer.&lt;/li&gt;
&lt;li&gt;EPANET patterns must use the same names as the selected demand fields.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Import the generated file in EPANET using &lt;b&gt;File &amp;gt; Import &amp;gt; Scenario&lt;/b&gt;.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Crea un archivo de escenario de demandas EPANET &lt;code&gt;.scn&lt;/code&gt;.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Cada categoría de demanda debe estar almacenada en un campo de la capa de nodos.&lt;/li&gt;
&lt;li&gt;Los patrones EPANET deben usar los mismos nombres que los campos de demanda seleccionados.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Importa el archivo generado en EPANET usando &lt;b&gt;File &amp;gt; Import &amp;gt; Scenario&lt;/b&gt;.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_demand_to_epanet_scenario.py" line="69"/>
        <source>Input node layer</source>
        <translation type="unfinished">Capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_demand_to_epanet_scenario.py" line="76"/>
        <source>Field containing demand</source>
        <translation type="unfinished">Campo que contiene la demanda</translation>
    </message>
    <message>
        <location filename="../processes/wnt_demand_to_epanet_scenario.py" line="86"/>
        <source>EPANET scenario file</source>
        <translation type="unfinished">Archivo de escenario EPANET</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_elevation_from_raster.py" line="64"/>
        <source>&lt;p&gt;Sets node elevations from a raster DEM.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Reads elevation values from the DEM at each node position.&lt;/li&gt;
&lt;li&gt;Writes the values to the selected elevation field.&lt;/li&gt;
&lt;li&gt;Nodes outside the raster extent are reported as skipped and kept unchanged.&lt;/li&gt;
&lt;li&gt;Can create a new output layer or update the input node layer.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_raster.py" line="79"/>
        <source>Node vector layer input</source>
        <translation type="unfinished">Capa vectorial de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_raster.py" line="86"/>
        <source>Elevation field.</source>
        <translation type="unfinished">Campo de elevación.</translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_raster.py" line="95"/>
        <source>DEM raster layer input</source>
        <translation type="unfinished">Capa ráster MDE de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_raster.py" line="101"/>
        <source>Output mode</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_raster.py" line="112"/>
        <source>Nodes with elevation layer</source>
        <translation type="unfinished">Capa de nodos con elevación</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="67"/>
        <source>&lt;p&gt;Sets node elevations from one or more LandXML TIN surfaces.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Surface names are written as a comma or semicolon separated list.&lt;/li&gt;
&lt;li&gt;If no surface is selected, the first TIN surface found in the file is used and reported.&lt;/li&gt;
&lt;li&gt;When several selected surfaces cover the same node, elevations must be consistent.&lt;/li&gt;
&lt;li&gt;Can create a new output layer or update the input node layer.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="82"/>
        <source>Node vector layer input</source>
        <translation type="unfinished">Capa vectorial de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="89"/>
        <source>Elevation field</source>
        <translation type="unfinished">Campo de elevación</translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="97"/>
        <source>LandXML file</source>
        <translation type="unfinished">Archivo LandXML</translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="104"/>
        <source>Surface names</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="113"/>
        <source>Output mode</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_elevation_from_tin.py" line="124"/>
        <source>Nodes with elevation layer</source>
        <translation type="unfinished">Capa de nodos con elevación</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_hydrant_pairs.py" line="66"/>
        <source>&lt;p&gt;Creates hydrant pairs from a hydrant node layer.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The output is a line layer connecting paired hydrants.&lt;/li&gt;
&lt;li&gt;The line geometry helps verify that pairs can be connected through public space.&lt;/li&gt;
&lt;li&gt;Pairs farther apart than the maximum separation are not generated.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Crea pares de hidrantes a partir de una capa de nodos de hidrantes.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;La salida es una capa de líneas que conecta los hidrantes emparejados.&lt;/li&gt;
&lt;li&gt;La geometría de las líneas ayuda a comprobar si los pares pueden conectarse por espacio público.&lt;/li&gt;
&lt;li&gt;No se generan pares separados por una distancia mayor que la separación máxima.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_hydrant_pairs.py" line="80"/>
        <source>Hydrant layer input</source>
        <translation type="unfinished">Capa de hidrantes de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_hydrant_pairs.py" line="87"/>
        <source>Hydrant ID field</source>
        <translation type="unfinished">Campo ID de hidrante</translation>
    </message>
    <message>
        <location filename="../processes/wnt_hydrant_pairs.py" line="95"/>
        <source>Maximum hydrant separation</source>
        <translation type="unfinished">Separación máxima entre hidrantes</translation>
    </message>
    <message>
        <location filename="../processes/wnt_hydrant_pairs.py" line="105"/>
        <source>Hydrant pairs layer</source>
        <translation type="unfinished">Capa de pares de hidrantes</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="243"/>
        <source>&lt;p&gt;Merges two networks from their node and link layers.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Nodes from the second network are connected to nodes from the first network when they are within the tolerance distance in the selected output CRS units.&lt;/li&gt;
&lt;li&gt;Connected nodes keep the &lt;code&gt;id&lt;/code&gt; and position of the first network node.&lt;/li&gt;
&lt;li&gt;Incident links from the second network are renamed and their endpoints are snapped to connected first-network nodes.&lt;/li&gt;
&lt;li&gt;Links from the second network must not already exist in the first network by &lt;code&gt;id&lt;/code&gt; or by matching endpoints within the tolerance distance.&lt;/li&gt;
&lt;li&gt;Near misses are reported when second-network nodes are closer than the configured near-merge factor times the tolerance.&lt;/li&gt;
&lt;li&gt;Output node and link layers are written in the selected CRS.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Validate the merged network after running this algorithm.&lt;/p&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="261"/>
        <source>First node layer input</source>
        <translation type="unfinished">Primera capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="268"/>
        <source>First link layer input</source>
        <translation type="unfinished">Primera capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="275"/>
        <source>Second node layer input</source>
        <translation type="unfinished">Segunda capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="282"/>
        <source>Second link layer input</source>
        <translation type="unfinished">Segunda capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="289"/>
        <source>Coordinate reference system (CRS)</source>
        <translation type="unfinished">Sistema de referencia de coordenadas (SRC)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="296"/>
        <source>Tolerance</source>
        <translation type="unfinished">Tolerancia</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="307"/>
        <source>Merged node layer</source>
        <translation type="unfinished">Capa de nodos fusionada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_merge_networks.py" line="313"/>
        <source>Merged link layer</source>
        <translation type="unfinished">Capa de links fusionada</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_from_epanet.py" line="319"/>
        <source>&lt;p&gt;Imports an EPANET &lt;code&gt;.inp&lt;/code&gt; file and creates node and link layers.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Node attributes are &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, &lt;code&gt;elevation&lt;/code&gt; and &lt;code&gt;epanet&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Link attributes are &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt; and &lt;code&gt;epanet&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;The &lt;code&gt;epanet&lt;/code&gt; field stores type-specific EPANET properties as JSON.&lt;/li&gt;
&lt;li&gt;Quality, source, mixing, reaction, status, energy, demand and tag data are preserved when present.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Importa un archivo &lt;code&gt;.inp&lt;/code&gt; de EPANET y crea capas de nodos y links.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Los atributos de nodos son &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, &lt;code&gt;elevation&lt;/code&gt; y &lt;code&gt;epanet&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Los atributos de links son &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt; y &lt;code&gt;epanet&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;El campo &lt;code&gt;epanet&lt;/code&gt; almacena en JSON las propiedades EPANET específicas de cada tipo.&lt;/li&gt;
&lt;li&gt;Los datos de calidad, fuente, mezcla, reacción, estado, energía, demanda y etiquetas se conservan cuando existen.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_epanet.py" line="334"/>
        <source>EPANET file</source>
        <translation type="unfinished">Archivo EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_epanet.py" line="341"/>
        <source>Coordinate reference system (CRS)</source>
        <translation type="unfinished">Sistema de referencia de coordenadas (SRC)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_epanet.py" line="348"/>
        <source>EPANET nodes</source>
        <translation type="unfinished">Nodos EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_epanet.py" line="354"/>
        <source>EPANET links</source>
        <translation type="unfinished">Líneas EPANET</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="138"/>
        <source>&lt;p&gt;Builds EPANET-style network node and link layers from input line features.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Output geometries are created in the selected coordinate reference system.&lt;/li&gt;
&lt;li&gt;Line endpoints closer than the tolerance are merged into a single node.&lt;/li&gt;
&lt;li&gt;The node layer contains &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, and &lt;code&gt;elevation&lt;/code&gt;; node type defaults to &lt;code&gt;JUNCTION&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;The link layer contains &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, and &lt;code&gt;length&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;When a &lt;code&gt;link_type&lt;/code&gt; field is selected, link type values are copied from the input features.&lt;/li&gt;
&lt;li&gt;Optional fields can add node degree and link topology data.&lt;/li&gt;
&lt;li&gt;Node elevations can be left at zero, copied from line endpoint Z values, sampled from a DEM raster, or interpolated from a LandXML TIN surface.&lt;/li&gt;
&lt;li&gt;Input layer fields are preserved in the output link layer.&lt;/li&gt;
&lt;li&gt;Multipart geometries are split into individual output links.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Looped lines are rejected.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Construye las dos capas: nodos y links de una red con estructura EPANET a partir de las líneas de entrada.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Las geometrías de salida se crean en el sistema de referencia de coordenadas seleccionado.&lt;/li&gt;
&lt;li&gt;Los extremos de líneas separados por una distancia menor que la tolerancia se fusionan en un único nodo.&lt;/li&gt;
&lt;li&gt;La capa de nodos contiene &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt; y &lt;code&gt;elevation&lt;/code&gt;; el tipo de nodo por defecto es &lt;code&gt;JUNCTION&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;La capa de links contiene &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt; y &lt;code&gt;length&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Cuando se selecciona un campo de tipo de link, se asigna a los links un tipo: &lt;code&gt;PIPE&lt;/code&gt;, &lt;code&gt;CV&lt;/code&gt;, &lt;code&gt;PUMP&lt;/code&gt;, &lt;code&gt;PRV&lt;/code&gt;, &lt;code&gt;PSV&lt;/code&gt;, &lt;code&gt;PBV&lt;/code&gt;, &lt;code&gt;FCV&lt;/code&gt;, &lt;code&gt;TCV&lt;/code&gt;, &lt;code&gt;GVP&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Con los campos opcionales se pueden añadir el grado de nodo y la topología de los links.&lt;/li&gt;
&lt;li&gt;Las elevaciones de nodos pueden dejarse a cero, copiarse desde los valores de elevación de los extremos de la capa de entrada, muestrearse desde un ráster DEM o interpolarse desde una superficie TIN LandXML.&lt;/li&gt;
&lt;li&gt;Los campos de la capa de entrada se conservan en la capa de links de salida.&lt;/li&gt;
&lt;li&gt;Las geometrías multiparte se separan en links de salida individuales.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Las líneas en bucle se rechazan.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="159"/>
        <source>Line vector layer input</source>
        <translation type="unfinished">Capa vectorial de líneas de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="166"/>
        <source>Coordinate reference system (CRS)</source>
        <translation type="unfinished">Sistema de referencia de coordenadas (SRC)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="173"/>
        <source>Minimum node separation, otherwise merge them</source>
        <translation type="unfinished">Separación mínima entre nodos; si no se cumple, se fusionan</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="183"/>
        <source>Node mask (P-$$-S generates P-01-S)</source>
        <translation type="unfinished">Máscara de nodos (P-$$-S genera P-01-S)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="190"/>
        <source>Number of the first node</source>
        <translation type="unfinished">Número del primer nodo</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="198"/>
        <source>Node numbering increment</source>
        <translation type="unfinished">Incremento de la numeración del nodo</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="206"/>
        <source>Link mask (P-$$-S generates P-01-S)</source>
        <translation type="unfinished">Máscara de links (P-$$-S genera P-01-S)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="213"/>
        <source>Number of first link</source>
        <translation type="unfinished">Número del primer link</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="221"/>
        <source>Link numbering increment</source>
        <translation type="unfinished">Incremento de la numeración del link</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="229"/>
        <source>Link type field</source>
        <translation type="unfinished">Campo de tipo de link</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="239"/>
        <source>Add node_degree field</source>
        <translation type="unfinished">Añade el grado a los nodos</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="246"/>
        <source>Add topology and zone fields</source>
        <translation type="unfinished">Añade topología y zona a los links</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="253"/>
        <source>Node elevation source</source>
        <translation type="unfinished">Añadir elevación a los nodos</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="262"/>
        <source>DEM raster layer input</source>
        <translation type="unfinished">Capa ráster MDE de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="269"/>
        <source>LandXML file</source>
        <translation type="unfinished">Archivo LandXML</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="277"/>
        <source>Surface name (if empty, first found)</source>
        <translation type="unfinished">Nombre de la superficie (si se deja vacío, se usa la primera)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="288"/>
        <source>Network node layer</source>
        <translation type="unfinished">Capa de nodos de la red</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="294"/>
        <source>Network link layer</source>
        <translation type="unfinished">Capa de links de la red</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="307"/>
        <source>Node numbering increment must be an integer different from 0</source>
        <translation type="unfinished">El incremento de la numeración del nodo debe ser un entero distinto de 0</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_lines.py" line="313"/>
        <source>Link numbering increment must be an integer different from 0</source>
        <translation type="unfinished">El incremento de la numeración del link debe ser un entero distinto de 0</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_from_xml.py" line="243"/>
        <source>&lt;p&gt;Imports network node and link layers from XML.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;&lt;code&gt;WNT Network XML&lt;/code&gt; files are loaded by network name and version; empty version loads the latest version for each selected network.&lt;/li&gt;
&lt;li&gt;&lt;code&gt;LandXML 1.2&lt;/code&gt; pipe networks are converted to WNT node and link layers.&lt;/li&gt;
&lt;li&gt;Network names are written as a comma or semicolon separated list. If empty, all networks are loaded.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_xml.py" line="252"/>
        <source>XML file</source>
        <translation type="unfinished">Archivo XML</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_xml.py" line="253"/>
        <source>Version id</source>
        <translation type="unfinished">Id de versión</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_xml.py" line="254"/>
        <source>Network names</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_xml.py" line="255"/>
        <source>Nodes</source>
        <translation type="unfinished">Nodos</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_from_xml.py" line="256"/>
        <source>Links</source>
        <translation type="unfinished">Links</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="76"/>
        <source>&lt;p&gt;Creates an EPANET &lt;code&gt;.inp&lt;/code&gt; file from network node and link layers.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Workflow A adds the selected node and link layers to an existing EPANET &lt;code&gt;.inp&lt;/code&gt; model; EPANET version and flow units are ignored.&lt;/li&gt;
&lt;li&gt;Workflow B creates a new EPANET model from a minimal internal template; select the EPANET version and flow units.&lt;/li&gt;
&lt;li&gt;Adds nodes to &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt;, or &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Adds links to &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt;, or &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Exports coordinates and intermediate vertices.&lt;/li&gt;
&lt;li&gt;Pipe diameter and roughness are not exported; add them using scenario files.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="93"/>
        <source>Input nodes layer</source>
        <translation type="unfinished">Capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="100"/>
        <source>Input links layer</source>
        <translation type="unfinished">Capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="107"/>
        <source>Workflow</source>
        <translation type="unfinished">Flujo de trabajo</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="116"/>
        <source>Existing EPANET model file</source>
        <translation type="unfinished">Archivo de modelo EPANET existente</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="124"/>
        <source>EPANET version</source>
        <translation type="unfinished">Versión de EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="133"/>
        <source>Flow units</source>
        <translation type="unfinished">Unidades de caudal</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="144"/>
        <source>EPANET model file</source>
        <translation type="unfinished">Archivo de modelo EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_epanet.py" line="159"/>
        <source>Existing EPANET model file is required for workflow A</source>
        <translation type="unfinished">El archivo de modelo EPANET existente es obligatorio para el flujo A</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_to_graph.py" line="57"/>
        <source>&lt;p&gt;Exports the network topology to a Trivial Graph Format file.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Input node and link layers must contain valid network identifiers.&lt;/li&gt;
&lt;li&gt;The output &lt;code&gt;.tgf&lt;/code&gt; file can be opened in graph tools such as yEd.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Exporta la topología de la red a un archivo en formato Trivial Graph Format.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Las capas de nodos y links de entrada deben contener identificadores de red válidos.&lt;/li&gt;
&lt;li&gt;El archivo &lt;code&gt;.tgf&lt;/code&gt; de salida puede abrirse en herramientas de grafos como yEd.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_graph.py" line="70"/>
        <source>Input node vector layer</source>
        <translation type="unfinished">Capa vectorial de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_graph.py" line="77"/>
        <source>Input link vector layer</source>
        <translation type="unfinished">Capa vectorial de líneas de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_graph.py" line="87"/>
        <source>Trivial Graph Format file</source>
        <translation type="unfinished">Archivo en formato TGF</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="82"/>
        <source>&lt;p&gt;Creates a pipesizing &lt;code&gt;.pro&lt;/code&gt; data file.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The required pressure must be stored in a node layer field.&lt;/li&gt;
&lt;li&gt;The pipe series name must be stored in a link layer field.&lt;/li&gt;
&lt;li&gt;The EPANET &lt;code&gt;.inp&lt;/code&gt; file path is written relative to the &lt;code&gt;.pro&lt;/code&gt; file.&lt;/li&gt;
&lt;li&gt;The pipe catalog is selected directly as an external &lt;code&gt;.cat&lt;/code&gt; file.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="92"/>
        <source>Input node layer</source>
        <translation type="unfinished">Capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="99"/>
        <source>Required pressure field</source>
        <translation type="unfinished">Campo de presión requerida</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="110"/>
        <source>Input link layer</source>
        <translation type="unfinished">Capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="117"/>
        <source>Pipe series field</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="127"/>
        <source>EPANET file</source>
        <translation type="unfinished">Archivo EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="134"/>
        <source>Pipesizing pipe catalog file</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_pipesizing.py" line="141"/>
        <source>Output pipesizing file</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="76"/>
        <source>&lt;p&gt;Creates a PPNO &lt;code&gt;.ext&lt;/code&gt; data file for pipe sizing.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The required pressure must be stored in a node layer field.&lt;/li&gt;
&lt;li&gt;The pipe group must be stored in a link layer field.&lt;/li&gt;
&lt;li&gt;The EPANET &lt;code&gt;.inp&lt;/code&gt; file must contain the model to optimize.&lt;/li&gt;
&lt;li&gt;The pipe catalog is selected directly as an external &lt;code&gt;.cat&lt;/code&gt; file.&lt;/li&gt;
&lt;li&gt;PPNO runs EPANET simulations, applies minimum pressure constraints, and optionally runs global optimization algorithms.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Crea un archivo de datos PPNO &lt;code&gt;.ext&lt;/code&gt; para dimensionar tuberías.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;La presión requerida debe estar almacenada en un campo de la capa de nodos.&lt;/li&gt;
&lt;li&gt;El grupo de tuberías debe estar almacenado en un campo de la capa de links.&lt;/li&gt;
&lt;li&gt;El archivo EPANET &lt;code&gt;.inp&lt;/code&gt; debe contener el modelo que se va a optimizar.&lt;/li&gt;
&lt;li&gt;El catálogo de tuberías se selecciona directamente como archivo externo &lt;code&gt;.cat&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;PPNO ejecuta simulaciones EPANET, aplica restricciones de presión mínima y opcionalmente ejecuta algoritmos de optimización global.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="92"/>
        <source>Input node layer</source>
        <translation type="unfinished">Capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="99"/>
        <source>Required pressure field</source>
        <translation type="unfinished">Campo de presión requerida</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="109"/>
        <source>Input link layer</source>
        <translation type="unfinished">Capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="116"/>
        <source>Pipe group field</source>
        <translation type="unfinished">Campo de grupo de tuberías</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="126"/>
        <source>Algorithms</source>
        <translation type="unfinished">Algoritmos</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="135"/>
        <source>EPANET file</source>
        <translation type="unfinished">Archivo EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="142"/>
        <source>PPNO pipe catalog file</source>
        <translation type="unfinished">Archivo de catálogo de tuberías PPNO</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_ppno.py" line="151"/>
        <source>Output ppno file</source>
        <translation type="unfinished">Archivo PPNO de salida</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="245"/>
        <source>&lt;p&gt;Exports network node and link layers to XML.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;&lt;code&gt;WNT Network XML&lt;/code&gt; stores topology and domain property bags using the network name as both network and version name.&lt;/li&gt;
&lt;li&gt;&lt;code&gt;LandXML 1.2&lt;/code&gt; writes a pipe network with the selected standard network type: sanitary, storm, water or other.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="253"/>
        <source>Input nodes layer</source>
        <translation type="unfinished">Capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="254"/>
        <source>Input links layer</source>
        <translation type="unfinished">Capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="255"/>
        <source>Network name</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="256"/>
        <source>Output format</source>
        <translation type="unfinished">Formato de salida</translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="257"/>
        <source>WNT model type</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="258"/>
        <source>LandXML network type</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_network_to_xml.py" line="259"/>
        <source>XML file</source>
        <translation type="unfinished">Archivo XML</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_node_degrees.py" line="63"/>
        <source>&lt;p&gt;Calculates the graph degree of each network node.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The degree is the number of links connected to a node.&lt;/li&gt;
&lt;li&gt;Orphan nodes have degree &lt;code&gt;0&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Leaf nodes have degree &lt;code&gt;1&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Continuity nodes have degree &lt;code&gt;2&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Can create a new output layer or update the input node layer.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Results are written to the &lt;code&gt;degree&lt;/code&gt; field.&lt;/p&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_node_degrees.py" line="80"/>
        <source>Network node layer input</source>
        <translation type="unfinished">Capa de nodos de la red de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_node_degrees.py" line="87"/>
        <source>Network links layer input</source>
        <translation type="unfinished">Capa de links de red de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_node_degrees.py" line="94"/>
        <source>Output mode</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_node_degrees.py" line="105"/>
        <source>Node degree layer</source>
        <translation type="unfinished">Capa de grados de nodo</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_pipe_propierties_to_epanet_scenario.py" line="58"/>
        <source>&lt;p&gt;Creates an EPANET &lt;code&gt;.scn&lt;/code&gt; scenario file with pipe diameters and roughness values.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Diameters are read from the selected mandatory diameter field.&lt;/li&gt;
&lt;li&gt;Roughness values are read from the selected mandatory roughness field.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Import the generated file in EPANET using &lt;b&gt;File &amp;gt; Import &amp;gt; Scenario&lt;/b&gt;.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Crea un archivo de escenario EPANET &lt;code&gt;.scn&lt;/code&gt; con diámetros y rugosidades de tuberías.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Los diámetros se leen desde el campo obligatorio de diámetro seleccionado.&lt;/li&gt;
&lt;li&gt;Las rugosidades se leen desde el campo obligatorio de rugosidad seleccionado.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Importa el archivo generado en EPANET usando &lt;b&gt;File &amp;gt; Import &amp;gt; Scenario&lt;/b&gt;.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_pipe_propierties_to_epanet_scenario.py" line="72"/>
        <source>Input link layer</source>
        <translation type="unfinished">Capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_pipe_propierties_to_epanet_scenario.py" line="79"/>
        <source>Diameter field</source>
        <translation type="unfinished">Campo de diámetro</translation>
    </message>
    <message>
        <location filename="../processes/wnt_pipe_propierties_to_epanet_scenario.py" line="87"/>
        <source>Roughness field</source>
        <translation type="unfinished">Campo de rugosidad</translation>
    </message>
    <message>
        <location filename="../processes/wnt_pipe_propierties_to_epanet_scenario.py" line="97"/>
        <source>EPANET scenario file</source>
        <translation type="unfinished">Archivo de escenario EPANET</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_results_from_epanet.py" line="62"/>
        <source>&lt;p&gt;Imports hydraulic results from an EPANET simulation.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Node results: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;demand&lt;/code&gt;, &lt;code&gt;head&lt;/code&gt;, &lt;code&gt;pressure&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Link results: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;flow&lt;/code&gt;, &lt;code&gt;velocity&lt;/code&gt;, &lt;code&gt;headloss&lt;/code&gt;, &lt;code&gt;status&lt;/code&gt;, &lt;code&gt;setting&lt;/code&gt;, &lt;code&gt;energy&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Configure the EPANET toolkit library before running this algorithm.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Importa resultados hidráulicos de una simulación de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Resultados de nodos: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;demand&lt;/code&gt;, &lt;code&gt;head&lt;/code&gt;, &lt;code&gt;pressure&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Resultados de links: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;flow&lt;/code&gt;, &lt;code&gt;velocity&lt;/code&gt;, &lt;code&gt;headloss&lt;/code&gt;, &lt;code&gt;status&lt;/code&gt;, &lt;code&gt;setting&lt;/code&gt;, &lt;code&gt;energy&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Configura la biblioteca del toolkit de EPANET antes de ejecutar este algoritmo.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_results_from_epanet.py" line="76"/>
        <source>EPANET file</source>
        <translation type="unfinished">Archivo EPANET</translation>
    </message>
    <message>
        <location filename="../processes/wnt_results_from_epanet.py" line="85"/>
        <source>Node results</source>
        <translation type="unfinished">Resultados de nodos</translation>
    </message>
    <message>
        <location filename="../processes/wnt_results_from_epanet.py" line="91"/>
        <source>Link results</source>
        <translation type="unfinished">Resultados de links</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="207"/>
        <source>&lt;p&gt;Splits line features at point positions.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Use this algorithm to insert junctions or intermediate nodes into line layers.&lt;/li&gt;
&lt;li&gt;Points are matched to lines using the tolerance in the selected output CRS units.&lt;/li&gt;
&lt;li&gt;Can create a new output layer or replace the input line layer features.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="221"/>
        <source>Input point layer</source>
        <translation type="unfinished">Capa de puntos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="228"/>
        <source>Input line layer</source>
        <translation type="unfinished">Capa de líneas de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="235"/>
        <source>Coordinate reference system (CRS)</source>
        <translation type="unfinished">Sistema de referencia de coordenadas (SRC)</translation>
    </message>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="242"/>
        <source>Tolerance</source>
        <translation type="unfinished">Tolerancia</translation>
    </message>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="252"/>
        <source>Output mode</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_split_lines_at_points.py" line="263"/>
        <source>Split line layer</source>
        <translation type="unfinished">Capa de líneas partidas</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_update_assignment.py" line="61"/>
        <source>&lt;p&gt;Updates demand assignments after editing assignment lines.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Recalculates demand values in the target node layer.&lt;/li&gt;
&lt;li&gt;Only the target endpoint of an assignment line can be moved.&lt;/li&gt;
&lt;li&gt;The source endpoint must remain on the original source feature.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Actualiza asignaciones de demanda después de editar líneas de asignación.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Recalcula los valores de demanda en la capa de nodos de destino.&lt;/li&gt;
&lt;li&gt;Solo puede moverse el extremo de destino de una línea de asignación.&lt;/li&gt;
&lt;li&gt;El extremo de origen debe permanecer sobre la entidad de origen original.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_update_assignment.py" line="75"/>
        <source>Source layer</source>
        <translation type="unfinished">Capa de origen</translation>
    </message>
    <message>
        <location filename="../processes/wnt_update_assignment.py" line="82"/>
        <source>Target layer</source>
        <translation type="unfinished">Capa de destino</translation>
    </message>
    <message>
        <location filename="../processes/wnt_update_assignment.py" line="89"/>
        <source>Edited assignment layer</source>
        <translation type="unfinished">Capa de asignaciones editada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_update_assignment.py" line="98"/>
        <source>Updated target layer</source>
        <translation type="unfinished">Capa de destino actualizada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_update_assignment.py" line="104"/>
        <source>Updated assignment layer</source>
        <translation type="unfinished">Capa de asignaciones actualizada</translation>
    </message>
</context>
<context>
    <name>WaterNetworkTools</name>
    <message>
        <location filename="../processes/wnt_validate.py" line="64"/>
        <source>&lt;p&gt;Analyses the network graph and reports topology problems.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Orphan nodes.&lt;/li&gt;
&lt;li&gt;Duplicate nodes.&lt;/li&gt;
&lt;li&gt;Links with undefined endpoints.&lt;/li&gt;
&lt;li&gt;Duplicate links.&lt;/li&gt;
&lt;li&gt;Loops, where start and end node are the same.&lt;/li&gt;
&lt;li&gt;Can create new output layers or update the input node and link layers.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Detected problems are written to the &lt;code&gt;problems&lt;/code&gt; field.&lt;/p&gt;
        </source>
        <translation type="unfinished">&lt;p&gt;Analiza el grafo de la red e informa de problemas topológicos.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Nodos huérfanos.&lt;/li&gt;
&lt;li&gt;Nodos duplicados.&lt;/li&gt;
&lt;li&gt;Links con extremos no definidos.&lt;/li&gt;
&lt;li&gt;Links duplicados.&lt;/li&gt;
&lt;li&gt;Bucles, donde el nodo inicial y final es el mismo.&lt;/li&gt;
&lt;li&gt;Puede crear nuevas capas de salida o actualizar las capas de nodos y links de entrada.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Los problemas detectados se escriben en el campo &lt;code&gt;problems&lt;/code&gt;.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="../processes/wnt_validate.py" line="82"/>
        <source>Input nodes layer</source>
        <translation type="unfinished">Capa de nodos de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_validate.py" line="89"/>
        <source>Input links layer</source>
        <translation type="unfinished">Capa de links de entrada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_validate.py" line="96"/>
        <source>Output mode</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../processes/wnt_validate.py" line="107"/>
        <source>Audited node layer</source>
        <translation type="unfinished">Capa de nodos auditada</translation>
    </message>
    <message>
        <location filename="../processes/wnt_validate.py" line="114"/>
        <source>Audited Link layer</source>
        <translation type="unfinished">Capa de links auditada</translation>
    </message>
</context>
</TS>
