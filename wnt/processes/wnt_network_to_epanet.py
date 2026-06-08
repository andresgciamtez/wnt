"""Export a network layer pair to an EPANET input file."""

import os
import tempfile

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm
from ..utils import utils_core as tools
from ..utils import utils_graph as graph
from .messages import crs as log_crs
from .messages import error, finish, info, start

class NetworkToEpanetAlgorithm(WntProcessingAlgorithm):
    """
    Build an EPANET model file from node and link layers.
    """

    # DEFINE CONSTANTS

    INPUT_NODES = 'INPUT_NODES'
    INPUT_LINES = 'INPUT_LINES'
    INPUT_EPANET = 'INPUT_EPANET'
    INPUT_TEMPLATE = INPUT_EPANET
    WORKFLOW = 'WORKFLOW'
    EPANET_VERSION = 'EPANET_VERSION'
    FLOW_UNITS = 'FLOW_UNITS'
    OUTPUT = 'OUTPUT'
    WORKFLOW_EXISTING = 0
    WORKFLOW_SCRATCH = 1
    WORKFLOW_OPTIONS = (
        'Add links and nodes to existing EPANET model',
        'Create EPANET model from scratch',
    )
    EPANET_VERSION_OPTIONS = ('2.00.12', '2.2+')
    FLOW_UNIT_OPTIONS = ('CFS', 'GPM', 'MGD', 'IMGD', 'AFD', 'LPS', 'LPM', 'MLD', 'CMH', 'CMD')


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return NetworkToEpanetAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_to_epanet'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Network to epanet file (.inp)'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return 'Export'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'export'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Creates an EPANET <code>.inp</code> file from network node and link layers.</p>
<ul>
<li>Output mode “Add links and nodes to existing EPANET model” adds the selected node and link layers to an existing EPANET <code>.inp</code> model; EPANET version and flow units are ignored.</li>
<li>Output mode “Create EPANET model from scratch” creates a new EPANET model from a minimal internal template; select the EPANET version and flow units.</li>
<li>Adds nodes to <code>JUNCTIONS</code>, <code>RESERVOIRS</code>, or <code>TANKS</code>.</li>
<li>Adds links to <code>PIPES</code>, <code>PUMPS</code>, or <code>VALVES</code>.</li>
<li>The final network graph is validated before writing the EPANET file.</li>
<li>Exports coordinates and intermediate vertices.</li>
<li>Pipe diameter and roughness are not exported; add them using scenario files.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES,
                self.tr('Input nodes layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Input links layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.WORKFLOW,
                self.tr('Output mode'),
                options=[self.tr(option) for option in self.WORKFLOW_OPTIONS],
                defaultValue=self.WORKFLOW_EXISTING,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_EPANET,
                self.tr('Existing EPANET model file'),
                extension='inp',
                optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.EPANET_VERSION,
                self.tr('EPANET version'),
                options=list(self.EPANET_VERSION_OPTIONS),
                defaultValue=1,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.FLOW_UNITS,
                self.tr('Flow units'),
                options=list(self.FLOW_UNIT_OPTIONS),
                defaultValue=self.FLOW_UNIT_OPTIONS.index('LPS'),
                optional=False
                )
            )

        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('EPANET model file'),
                fileFilter='*.inp'
                )
            )

    def checkParameterValues(self, parameters, context):
        """
        Validate workflow-dependent parameters before running.
        """
        workflow = self.parameterAsEnum(parameters, self.WORKFLOW, context)
        epanet_file = self.parameterAsFile(parameters, self.INPUT_EPANET, context)
        if workflow == self.WORKFLOW_EXISTING and not epanet_file:
            return False, self.tr('Existing EPANET model file is required for this output mode')
        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        workflow = self.parameterAsEnum(parameters, self.WORKFLOW, context)
        epanet_file = self.parameterAsFile(parameters, self.INPUT_EPANET, context)
        epanet_version = self.parameterAsEnum(parameters, self.EPANET_VERSION, context)
        flow_units = self.parameterAsEnum(parameters, self.FLOW_UNITS, context)

        # CHECK CRS
        crs = nodes.sourceCrs()
        if crs == links.sourceCrs():

            # SEND INFORMATION TO THE USER
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
            return {}

        # OUTPUT
        EPANET = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # BUILD NETWORK
        newnet = tools.WntNetwork()

        # NODES
        ncnt = 0
        for f in nodes.getFeatures():
            ncnt += 1
            newnode = tools.WntNode(f['id'])
            newnode.from_wkt(f.geometry().asWkt())
            newnode.set_type(f['type'])
            newnode.set_elevation(f['elevation'])
            newnet.add_node(newnode)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/nodes.featureCount())

        # LINKS
        lcnt = 0
        for f in links.getFeatures():
            lcnt += 1
            newlink = tools.WntLink(f['id'], f['start'], f['end'])
            newlink.from_wkt(f.geometry().asWkt())
            newlink.epanet['length'] = f['length']
            newlink.set_type(f['type'])
            newnet.add_link(newlink)

            # SHOW POROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/links.featureCount())

        # WRITE NET
        template_file = epanet_file
        cleanup_template = None
        if workflow == self.WORKFLOW_EXISTING:
            if not template_file:
                error(feedback, "Existing EPANET model file is required for this output mode")
                return {}
            try:
                base_net = tools.WntNetwork()
                base_net.from_epanet(template_file)
            except Exception as exc:
                error(feedback, "Could not read existing EPANET model file: " + str(exc))
                return {}
            problems = self._network_problems([base_net, newnet])
            if self._has_graph_problems(problems):
                error(feedback, "Merged EPANET network is not valid: " + self._problem_text(problems))
                return {}
            info(feedback, "Output mode", self.WORKFLOW_OPTIONS[self.WORKFLOW_EXISTING])
            info(feedback, "Existing EPANET model file", template_file)
        else:
            version_label = self.EPANET_VERSION_OPTIONS[epanet_version]
            flow_unit_label = self.FLOW_UNIT_OPTIONS[flow_units]
            template_file = self._create_minimal_template(version_label, flow_unit_label)
            cleanup_template = template_file
            problems = self._network_problems([newnet])
            if self._has_graph_problems(problems):
                error(feedback, "EPANET network is not valid: " + self._problem_text(problems))
                return {}
            info(feedback, "Output mode", self.WORKFLOW_OPTIONS[self.WORKFLOW_SCRATCH])
            info(feedback, "EPANET version", version_label)
            info(feedback, "Flow units", flow_unit_label)

        try:
            newnet.to_epanet(EPANET, template_file)
        finally:
            if cleanup_template:
                try:
                    os.unlink(cleanup_template)
                except OSError:
                    pass

        # SHOW INFO
        info(feedback, "Nodes exported", ncnt)
        info(feedback, "Links exported", lcnt)
        info(feedback, "Output file", EPANET)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: EPANET}

    @staticmethod
    def _network_problems(networks):
        """Return graph validation problems for one or more WntNetwork objects."""
        node_ids = []
        links = []
        for network in networks:
            node_ids.extend(node.name() for node in network.nodes())
            links.extend((link.name(), link.start(), link.end()) for link in network.links())
        return graph.validate_records(node_ids, links)

    @staticmethod
    def _has_graph_problems(problems):
        return any(bool(values) for values in problems.values())

    @staticmethod
    def _problem_text(problems):
        parts = []
        for name, values in problems.items():
            if values:
                parts.append("{}: {}".format(name, ", ".join(sorted(str(value) for value in values))))
        return "; ".join(parts)

    @classmethod
    def _create_minimal_template(cls, version, flow_units):
        """Create a temporary EPANET template with the sections used by the exporter."""
        handle = tempfile.NamedTemporaryFile(
            mode='w',
            encoding='latin-1',
            suffix='.inp',
            delete=False,
        )
        try:
            handle.write(cls._minimal_template_text(version, flow_units))
            return handle.name
        finally:
            handle.close()

    @staticmethod
    def _minimal_template_text(version, flow_units):
        """Return a minimal EPANET INP template for a new model."""
        options = [
            f'UNITS {flow_units}',
            'HEADLOSS H-W',
        ]
        if version == '2.2+':
            options.extend([
                'DEMAND MODEL DDA',
                'MINIMUM PRESSURE 0',
                'REQUIRED PRESSURE 0.1',
                'PRESSURE EXPONENT 0.5',
            ])
        option_lines = '\n'.join(options)
        return (
            '[TITLE]\n'
            '; File generated automatically by Water Network Tools\n'
            '[JUNCTIONS]\n'
            '[RESERVOIRS]\n'
            '[TANKS]\n'
            '[PIPES]\n'
            '[PUMPS]\n'
            '[VALVES]\n'
            '[COORDINATES]\n'
            '[VERTICES]\n'
            '[BACKDROP]\n'
            'DIMENSIONS 0 0 0 0\n'
            '[OPTIONS]\n'
            f'{option_lines}\n'
            '[END]\n'
        )
