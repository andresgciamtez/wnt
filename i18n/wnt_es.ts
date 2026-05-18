<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="es">
<context>
    <name>WaterNetworkTools</name>
    <message>
        <source>&lt;p&gt;Analyses the network graph and reports topology problems.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Orphan nodes.&lt;/li&gt;
&lt;li&gt;Duplicate nodes.&lt;/li&gt;
&lt;li&gt;Links with undefined endpoints.&lt;/li&gt;
&lt;li&gt;Duplicate links.&lt;/li&gt;
&lt;li&gt;Loops, where start and end node are the same.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Detected problems are written to the &lt;code&gt;problems&lt;/code&gt; field.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Analiza el grafo de la red e informa de problemas topológicos.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Nodos huérfanos.&lt;/li&gt;
&lt;li&gt;Nodos duplicados.&lt;/li&gt;
&lt;li&gt;Líneas con extremos no definidos.&lt;/li&gt;
&lt;li&gt;Líneas duplicadas.&lt;/li&gt;
&lt;li&gt;Bucles, donde el nodo inicial y final son el mismo.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Los problemas detectados se escriben en el campo &lt;code&gt;problems&lt;/code&gt;.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Assigns demand from a &lt;b&gt;source layer&lt;/b&gt; to a &lt;b&gt;target node layer&lt;/b&gt; using the nearest target feature.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Both input layers must contain an &lt;code&gt;id&lt;/code&gt; field.&lt;/li&gt;
&lt;li&gt;The selected source demand fields are copied and accumulated in the target layer.&lt;/li&gt;
&lt;li&gt;The output assignment layer stores the connection lines between source and target features.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Use &lt;b&gt;Update assignment&lt;/b&gt; after editing assignment lines.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Asigna demandas desde una &lt;b&gt;capa de origen&lt;/b&gt; a una &lt;b&gt;capa de nodos de destino&lt;/b&gt; usando la entidad de destino más cercana.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Ambas capas de entrada deben contener un campo &lt;code&gt;id&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Los campos de demanda seleccionados de la capa de origen se copian y acumulan en la capa de destino.&lt;/li&gt;
&lt;li&gt;La capa de asignaciones de salida almacena las líneas de conexión entre las entidades de origen y destino.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Usa &lt;b&gt;Update assignment&lt;/b&gt; después de editar las líneas de asignación.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Builds EPANET-style network node and link layers from input line features.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Line endpoints closer than the tolerance are merged into a single node.&lt;/li&gt;
&lt;li&gt;The node layer contains &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, and &lt;code&gt;elevation&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;The link layer contains &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, and &lt;code&gt;length&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Input layer fields are preserved in the output link layer.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Limitations: multipart geometries and Z values are not supported. Looped lines are rejected.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Construye capas de nodos y líneas de red con estructura EPANET a partir de las líneas de entrada.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Los extremos de líneas separados por una distancia menor que la tolerancia se fusionan en un único nodo.&lt;/li&gt;
&lt;li&gt;La capa de nodos contiene &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt; y &lt;code&gt;elevation&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;La capa de líneas contiene &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt; y &lt;code&gt;length&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Los campos de la capa de entrada se conservan en la capa de líneas de salida.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Limitaciones: no se admiten geometrías multiparte ni valores Z. Las líneas en bucle se rechazan.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Calculates the graph degree of each network node.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The degree is the number of links connected to a node.&lt;/li&gt;
&lt;li&gt;Orphan nodes have degree &lt;code&gt;0&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Leaf nodes have degree &lt;code&gt;1&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Continuity nodes have degree &lt;code&gt;2&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Results are written to the &lt;code&gt;degree&lt;/code&gt; field.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Calcula el grado de grafo de cada nodo de la red.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;El grado es el número de líneas conectadas a un nodo.&lt;/li&gt;
&lt;li&gt;Los nodos huérfanos tienen grado &lt;code&gt;0&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Los nodos hoja tienen grado &lt;code&gt;1&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Los nodos de continuidad tienen grado &lt;code&gt;2&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Los resultados se escriben en el campo &lt;code&gt;degree&lt;/code&gt;.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Classifies network links into branched and meshed areas.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Adds &lt;code&gt;graph_type&lt;/code&gt;: &lt;code&gt;BRANCHED&lt;/code&gt; or &lt;code&gt;MESHED&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Adds &lt;code&gt;sub&lt;/code&gt;: subnetwork identifier.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Use this algorithm to support network sectorization.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Clasifica las líneas de la red en zonas ramificadas y malladas.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Añade el campo &lt;code&gt;graph_type&lt;/code&gt;: &lt;code&gt;BRANCHED&lt;/code&gt; o &lt;code&gt;MESHED&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Añade el campo &lt;code&gt;sub&lt;/code&gt;: identificador de subred.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Usa este algoritmo como apoyo para la sectorización de redes.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Connects features from a &lt;b&gt;source layer&lt;/b&gt; to a &lt;b&gt;target layer&lt;/b&gt; by minimum distance.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Both layers must contain an &lt;code&gt;id&lt;/code&gt; field.&lt;/li&gt;
&lt;li&gt;The maximum number of connections and maximum distance limit the generated links.&lt;/li&gt;
&lt;li&gt;The output is a line layer representing the connections.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Conecta entidades de una &lt;b&gt;capa de origen&lt;/b&gt; con una &lt;b&gt;capa de destino&lt;/b&gt; por distancia mínima.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Ambas capas deben contener un campo &lt;code&gt;id&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;El número máximo de conexiones y la distancia máxima limitan las líneas generadas.&lt;/li&gt;
&lt;li&gt;La salida es una capa de líneas que representa las conexiones.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Creates a PPNO &lt;code&gt;.ext&lt;/code&gt; data file for pipe sizing.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The required pressure must be stored in a node layer field.&lt;/li&gt;
&lt;li&gt;The pipe series must be stored in a link layer field.&lt;/li&gt;
&lt;li&gt;The EPANET &lt;code&gt;.inp&lt;/code&gt; file must contain the model to optimize.&lt;/li&gt;
&lt;li&gt;The PPNO template must contain the available pipe series.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Crea un archivo de datos &lt;code&gt;.ext&lt;/code&gt; de PPNO para dimensionar tuberías.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;La presión requerida debe estar almacenada en un campo de la capa de nodos.&lt;/li&gt;
&lt;li&gt;La serie de tuberías debe estar almacenada en un campo de la capa de líneas.&lt;/li&gt;
&lt;li&gt;El archivo &lt;code&gt;.inp&lt;/code&gt; de EPANET debe contener el modelo que se va a optimizar.&lt;/li&gt;
&lt;li&gt;La plantilla PPNO debe contener las series de tuberías disponibles.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Creates an EPANET &lt;code&gt;.inp&lt;/code&gt; file from network node and link layers and an EPANET template.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Adds nodes to &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt;, or &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Adds links to &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt;, or &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Exports coordinates and intermediate vertices.&lt;/li&gt;
&lt;li&gt;Pipe diameter and roughness are not exported; add them using scenario files.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Crea un archivo &lt;code&gt;.inp&lt;/code&gt; de EPANET a partir de capas de nodos y líneas de red y una plantilla de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Añade nodos a &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt; o &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Añade líneas a &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt; o &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Exporta coordenadas y vértices intermedios.&lt;/li&gt;
&lt;li&gt;No exporta diámetro ni rugosidad de tuberías; añádelos mediante archivos de escenario.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Creates an EPANET demand scenario file.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Each demand category must be stored in a field of the node layer.&lt;/li&gt;
&lt;li&gt;EPANET patterns must use the same names as the selected demand fields.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Import the generated file in EPANET using &lt;b&gt;File &amp;gt; Import &amp;gt; Scenario&lt;/b&gt;.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Crea un archivo &lt;code&gt;.inp&lt;/code&gt; de EPANET a partir de capas de nodos y líneas de red y una plantilla de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Añade nodos a &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt; o &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Añade líneas a &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt; o &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Exporta coordenadas y vértices intermedios.&lt;/li&gt;
&lt;li&gt;No exporta diámetro ni rugosidad de tuberías; añádelos mediante archivos de escenario.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Creates an EPANET scenario file for pipe diameters and roughness values.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Diameters are read from the selected diameter field.&lt;/li&gt;
&lt;li&gt;Roughness values are read from the selected roughness field.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Import the generated file in EPANET using &lt;b&gt;File &amp;gt; Import &amp;gt; Scenario&lt;/b&gt;.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Crea un archivo &lt;code&gt;.inp&lt;/code&gt; de EPANET a partir de capas de nodos y líneas de red y una plantilla de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Añade nodos a &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt; o &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Añade líneas a &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt; o &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Exporta coordenadas y vértices intermedios.&lt;/li&gt;
&lt;li&gt;No exporta diámetro ni rugosidad de tuberías; añádelos mediante archivos de escenario.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Creates hydrant pairs from a hydrant node layer.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The output is a line layer connecting paired hydrants.&lt;/li&gt;
&lt;li&gt;The line geometry helps verify that pairs can be connected through public space.&lt;/li&gt;
&lt;li&gt;Hydrants farther apart than the maximum separation are ignored.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Crea pares de hidrantes a partir de una capa de nodos de hidrantes.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;La salida es una capa de líneas que conecta los hidrantes emparejados.&lt;/li&gt;
&lt;li&gt;La geometría de las líneas ayuda a comprobar si los pares pueden conectarse por espacio público.&lt;/li&gt;
&lt;li&gt;Los hidrantes separados por una distancia mayor que la separación máxima se ignoran.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Exports the network topology to a Trivial Graph Format file.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Input node and link layers must contain valid network identifiers.&lt;/li&gt;
&lt;li&gt;The output &lt;code&gt;.tgf&lt;/code&gt; file can be opened in graph tools such as yEd.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Exporta la topología de la red a un archivo en formato Trivial Graph Format.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Las capas de nodos y líneas de entrada deben contener identificadores de red válidos.&lt;/li&gt;
&lt;li&gt;El archivo &lt;code&gt;.tgf&lt;/code&gt; de salida puede abrirse en herramientas de grafos como yEd.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Imports an EPANET &lt;code&gt;.inp&lt;/code&gt; file and creates node and link layers.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Node attributes: &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, &lt;code&gt;elevation&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Link attributes: &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, &lt;code&gt;length&lt;/code&gt;, &lt;code&gt;diameter&lt;/code&gt;, &lt;code&gt;roughness&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Supported node sections: &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt;, &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Supported link sections: &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt;, &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Importa un archivo &lt;code&gt;.inp&lt;/code&gt; de EPANET y crea capas de nodos y líneas.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Atributos de nodos: &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, &lt;code&gt;elevation&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Atributos de líneas: &lt;code&gt;id&lt;/code&gt;, &lt;code&gt;start&lt;/code&gt;, &lt;code&gt;end&lt;/code&gt;, &lt;code&gt;type&lt;/code&gt;, &lt;code&gt;length&lt;/code&gt;, &lt;code&gt;diameter&lt;/code&gt;, &lt;code&gt;roughness&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Secciones de nodos admitidas: &lt;code&gt;JUNCTIONS&lt;/code&gt;, &lt;code&gt;RESERVOIRS&lt;/code&gt;, &lt;code&gt;TANKS&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Secciones de líneas admitidas: &lt;code&gt;PIPES&lt;/code&gt;, &lt;code&gt;PUMPS&lt;/code&gt;, &lt;code&gt;VALVES&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Imports hydraulic results from an EPANET simulation.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Node results: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;demand&lt;/code&gt;, &lt;code&gt;head&lt;/code&gt;, &lt;code&gt;pressure&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Link results: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;flow&lt;/code&gt;, &lt;code&gt;velocity&lt;/code&gt;, &lt;code&gt;headloss&lt;/code&gt;, &lt;code&gt;status&lt;/code&gt;, &lt;code&gt;setting&lt;/code&gt;, &lt;code&gt;energy&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Configure the EPANET toolkit library before running this algorithm.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Importa resultados hidráulicos de una simulación de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Resultados de nodos: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;demand&lt;/code&gt;, &lt;code&gt;head&lt;/code&gt;, &lt;code&gt;pressure&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Resultados de líneas: &lt;code&gt;time&lt;/code&gt;, &lt;code&gt;flow&lt;/code&gt;, &lt;code&gt;velocity&lt;/code&gt;, &lt;code&gt;headloss&lt;/code&gt;, &lt;code&gt;status&lt;/code&gt;, &lt;code&gt;setting&lt;/code&gt;, &lt;code&gt;energy&lt;/code&gt;.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Configura la biblioteca del toolkit de EPANET antes de ejecutar este algoritmo.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Imports pipe networks from a LandXML 1.2 file.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Creates node and link layers from the LandXML pipe network definitions.&lt;/li&gt;
&lt;li&gt;Uses the CRS information stored in the LandXML file when available.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Importa redes de tuberías desde un archivo LandXML 1.2.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Crea capas de nodos y líneas a partir de las definiciones de redes de tuberías del archivo LandXML.&lt;/li&gt;
&lt;li&gt;Usa la información de SRC almacenada en el archivo LandXML cuando está disponible.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Merges two networks from their node and link layers.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Connection nodes must share the same &lt;code&gt;id&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;The merge is created even when matching connection nodes are not coincident.&lt;/li&gt;
&lt;li&gt;The maximum connection distance is reported in the log.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Validate the merged network after running this algorithm.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Fusiona dos redes a partir de sus capas de nodos y líneas.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Los nodos de conexión deben compartir el mismo &lt;code&gt;id&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;La fusión se crea aunque los nodos de conexión coincidentes no sean coincidentes geométricamente.&lt;/li&gt;
&lt;li&gt;La distancia máxima de conexión se informa en el registro.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Valida la red fusionada después de ejecutar este algoritmo.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Sets node elevations from a LandXML TIN surface.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Reads the selected LandXML surface, or the first surface when no name is provided.&lt;/li&gt;
&lt;li&gt;Interpolates elevations at node positions.&lt;/li&gt;
&lt;li&gt;Writes the values to the selected elevation field.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Asigna elevaciones a los nodos desde una superficie TIN LandXML.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Lee la superficie LandXML seleccionada o la primera superficie si no se indica ningún nombre.&lt;/li&gt;
&lt;li&gt;Interpola las elevaciones en las posiciones de los nodos.&lt;/li&gt;
&lt;li&gt;Escribe los valores en el campo de elevación seleccionado.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Sets node elevations from a raster DEM.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Reads elevation values from the DEM at each node position.&lt;/li&gt;
&lt;li&gt;Writes the values to the selected elevation field.&lt;/li&gt;
&lt;li&gt;Nodes outside the raster extent are reported as skipped.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Asigna elevaciones a los nodos desde un MDE ráster.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Lee los valores de elevación del MDE en la posición de cada nodo.&lt;/li&gt;
&lt;li&gt;Escribe los valores en el campo de elevación seleccionado.&lt;/li&gt;
&lt;li&gt;Los nodos situados fuera de la extensión del ráster se notifican como omitidos.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Sets the path to the EPANET toolkit library.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;The path is stored in &lt;code&gt;toolkit.ini&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Configure this before importing EPANET simulation results.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;EPANET toolkit libraries can be obtained from the EPA EPANET download page or from a compatible EPANET toolkit build.&lt;/p&gt;
        </source>
        <translation>&lt;p&gt;Define la ruta de la biblioteca del toolkit de EPANET.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;La ruta se guarda en &lt;code&gt;toolkit.ini&lt;/code&gt;.&lt;/li&gt;
&lt;li&gt;Configúrala antes de importar resultados de simulaciones de EPANET.&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;Las bibliotecas del toolkit de EPANET pueden obtenerse desde la página de descargas de EPANET de la EPA o desde una compilación compatible del toolkit de EPANET.&lt;/p&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Splits line features at point positions.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Use this algorithm to insert junctions or intermediate nodes into line layers.&lt;/li&gt;
&lt;li&gt;Points are matched to lines using the tolerance distance.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Parte entidades de línea en posiciones de puntos.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Usa este algoritmo para insertar uniones o nodos intermedios en capas de líneas.&lt;/li&gt;
&lt;li&gt;Los puntos se ajustan a las líneas usando la distancia de tolerancia.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>&lt;p&gt;Updates demand assignments after editing assignment lines.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Recalculates demand values in the target node layer.&lt;/li&gt;
&lt;li&gt;Only the target endpoint of an assignment line can be moved.&lt;/li&gt;
&lt;li&gt;The source endpoint must remain on the original source feature.&lt;/li&gt;
&lt;/ul&gt;
        </source>
        <translation>&lt;p&gt;Actualiza asignaciones de demanda después de editar líneas de asignación.&lt;/p&gt;
&lt;ul&gt;
&lt;li&gt;Recalcula los valores de demanda en la capa de nodos de destino.&lt;/li&gt;
&lt;li&gt;Solo puede moverse el extremo de destino de una línea de asignación.&lt;/li&gt;
&lt;li&gt;El extremo de origen debe permanecer sobre la entidad de origen original.&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <source>Assignment layer</source>
        <translation>Capa de asignaciones</translation>
    </message>
    <message>
        <source>Audited Link layer</source>
        <translation>Capa de líneas auditada</translation>
    </message>
    <message>
        <source>Audited node layer</source>
        <translation>Capa de nodos auditada</translation>
    </message>
    <message>
        <source>Connection layer</source>
        <translation>Capa de conexiones</translation>
    </message>
    <message>
        <source>Coordinate reference system (CRS)</source>
        <translation>Sistema de referencia de coordenadas (SRC)</translation>
    </message>
    <message>
        <source>DEM raster layer input</source>
        <translation>Capa ráster MDE de entrada</translation>
    </message>
    <message>
        <source>Diameter field</source>
        <translation>Campo de diámetro</translation>
    </message>
    <message>
        <source>Edited assignment layer</source>
        <translation>Capa de asignaciones editada</translation>
    </message>
    <message>
        <source>Elevation field</source>
        <translation>Campo de elevación</translation>
    </message>
    <message>
        <source>Elevation field.</source>
        <translation>Campo de elevación.</translation>
    </message>
    <message>
        <source>Epanet file</source>
        <translation>Archivo EPANET</translation>
    </message>
    <message>
        <source>Epanet lib</source>
        <translation>Biblioteca EPANET</translation>
    </message>
    <message>
        <source>Epanet links</source>
        <translation>Líneas EPANET</translation>
    </message>
    <message>
        <source>Epanet model file</source>
        <translation>Archivo de modelo EPANET</translation>
    </message>
    <message>
        <source>Epanet nodes</source>
        <translation>Nodos EPANET</translation>
    </message>
    <message>
        <source>Epanet scenario file</source>
        <translation>Archivo de escenario EPANET</translation>
    </message>
    <message>
        <source>Epanet template file</source>
        <translation>Archivo de plantilla EPANET</translation>
    </message>
    <message>
        <source>Field containing demand</source>
        <translation>Campo que contiene la demanda</translation>
    </message>
    <message>
        <source>First link layer input</source>
        <translation>Primera capa de líneas de entrada</translation>
    </message>
    <message>
        <source>First node layer input</source>
        <translation>Primera capa de nodos de entrada</translation>
    </message>
    <message>
        <source>Hydrant ID field</source>
        <translation>Campo ID de hidrante</translation>
    </message>
    <message>
        <source>Hydrant layer input</source>
        <translation>Capa de hidrantes de entrada</translation>
    </message>
    <message>
        <source>Hydrant pairs layer</source>
        <translation>Capa de pares de hidrantes</translation>
    </message>
    <message>
        <source>Input line layer</source>
        <translation>Capa de líneas de entrada</translation>
    </message>
    <message>
        <source>Input link layer</source>
        <translation>Capa de líneas de entrada</translation>
    </message>
    <message>
        <source>Input link vector layer</source>
        <translation>Capa vectorial de líneas de entrada</translation>
    </message>
    <message>
        <source>Input links layer</source>
        <translation>Capa de líneas de entrada</translation>
    </message>
    <message>
        <source>Input node layer</source>
        <translation>Capa de nodos de entrada</translation>
    </message>
    <message>
        <source>Input node vector layer</source>
        <translation>Capa vectorial de nodos de entrada</translation>
    </message>
    <message>
        <source>Input nodes layer</source>
        <translation>Capa de nodos de entrada</translation>
    </message>
    <message>
        <source>Input point layer</source>
        <translation>Capa de puntos de entrada</translation>
    </message>
    <message>
        <source>LandXML file</source>
        <translation>Archivo LandXML</translation>
    </message>
    <message>
        <source>Line vector layer input</source>
        <translation>Capa vectorial de líneas de entrada</translation>
    </message>
    <message>
        <source>Link increment</source>
        <translation>Incremento de líneas</translation>
    </message>
    <message>
        <source>Link mask (P-$$-S generates P-01-S)</source>
        <translation>Máscara de líneas (P-$$-S genera P-01-S)</translation>
    </message>
    <message>
        <source>Link results</source>
        <translation>Resultados de líneas</translation>
    </message>
    <message>
        <source>Links</source>
        <translation>Líneas</translation>
    </message>
    <message>
        <source>Max distance</source>
        <translation>Distancia máxima</translation>
    </message>
    <message>
        <source>Max number of connections</source>
        <translation>Número máximo de conexiones</translation>
    </message>
    <message>
        <source>Maximum hydrant separation</source>
        <translation>Separación máxima entre hidrantes</translation>
    </message>
    <message>
        <source>Merged link layer</source>
        <translation>Capa de líneas fusionada</translation>
    </message>
    <message>
        <source>Merged node layer</source>
        <translation>Capa de nodos fusionada</translation>
    </message>
    <message>
        <source>Minimum node separation, otherwise merge them</source>
        <translation>Separación mínima entre nodos; si no se cumple, se fusionan</translation>
    </message>
    <message>
        <source>Network link layer</source>
        <translation>Capa de líneas de red</translation>
    </message>
    <message>
        <source>Network links layer input</source>
        <translation>Capa de líneas de red de entrada</translation>
    </message>
    <message>
        <source>Network node layer</source>
        <translation>Capa de nodos de red</translation>
    </message>
    <message>
        <source>Network node layer input</source>
        <translation>Capa de nodos de red de entrada</translation>
    </message>
    <message>
        <source>Node degree layer</source>
        <translation>Capa de grados de nodo</translation>
    </message>
    <message>
        <source>Node increment</source>
        <translation>Incremento de nodos</translation>
    </message>
    <message>
        <source>Node mask (P-$$-S generates P-01-S)</source>
        <translation>Máscara de nodos (P-$$-S genera P-01-S)</translation>
    </message>
    <message>
        <source>Node results</source>
        <translation>Resultados de nodos</translation>
    </message>
    <message>
        <source>Node vector layer input</source>
        <translation>Capa vectorial de nodos de entrada</translation>
    </message>
    <message>
        <source>Nodes</source>
        <translation>Nodos</translation>
    </message>
    <message>
        <source>Nodes with elevation layer</source>
        <translation>Capa de nodos con elevación</translation>
    </message>
    <message>
        <source>Number of first link</source>
        <translation>Número de la primera línea</translation>
    </message>
    <message>
        <source>Number of the first node</source>
        <translation>Número del primer nodo</translation>
    </message>
    <message>
        <source>Output ppno file</source>
        <translation>Archivo PPNO de salida</translation>
    </message>
    <message>
        <source>Pipe series field</source>
        <translation>Campo de serie de tuberías</translation>
    </message>
    <message>
        <source>ppno template file</source>
        <translation>Archivo de plantilla PPNO</translation>
    </message>
    <message>
        <source>Required pressure field</source>
        <translation>Campo de presión requerida</translation>
    </message>
    <message>
        <source>Roughness field</source>
        <translation>Campo de rugosidad</translation>
    </message>
    <message>
        <source>Second link layer input</source>
        <translation>Segunda capa de líneas de entrada</translation>
    </message>
    <message>
        <source>Second node layer input</source>
        <translation>Segunda capa de nodos de entrada</translation>
    </message>
    <message>
        <source>Source demand fields</source>
        <translation>Campos de demanda de origen</translation>
    </message>
    <message>
        <source>Source layer</source>
        <translation>Capa de origen</translation>
    </message>
    <message>
        <source>Split line layer</source>
        <translation>Capa de líneas partidas</translation>
    </message>
    <message>
        <source>Subnetwork link layer</source>
        <translation>Capa de líneas de subred</translation>
    </message>
    <message>
        <source>Surface name (if empty, first found)</source>
        <translation>Nombre de la superficie (si se deja vacío, se usa la primera)</translation>
    </message>
    <message>
        <source>Target layer</source>
        <translation>Capa de destino</translation>
    </message>
    <message>
        <source>Target with demands layer</source>
        <translation>Capa de destino con demandas</translation>
    </message>
    <message>
        <source>Tolerance distance</source>
        <translation>Distancia de tolerancia</translation>
    </message>
    <message>
        <source>Trivial Graph Format file</source>
        <translation>Archivo en formato TGF</translation>
    </message>
    <message>
        <source>Updated assignment layer</source>
        <translation>Capa de asignaciones actualizada</translation>
    </message>
    <message>
        <source>Updated target layer</source>
        <translation>Capa de destino actualizada</translation>
    </message>
</context>
</TS>
