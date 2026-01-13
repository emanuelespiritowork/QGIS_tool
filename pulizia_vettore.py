"""
Model exported as python.
Name : pulizia_vettore
Group : 
With QGIS : 34007
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Pulizia_vettore(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('input', 'input', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Output', 'output', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}

        # Ripara geometrie
        alg_params = {
            'INPUT': parameters['input'],
            'METHOD': 1,  # Struttura
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RiparaGeometrie'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Elimina geometrie duplicate
        alg_params = {
            'INPUT': outputs['RiparaGeometrie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EliminaGeometrieDuplicate'] = processing.run('native:deleteduplicategeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Rimuovi i vertici duplicati
        alg_params = {
            'INPUT': outputs['EliminaGeometrieDuplicate']['OUTPUT'],
            'TOLERANCE': 1e-06,
            'USE_Z_VALUE': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RimuoviIVerticiDuplicati'] = processing.run('native:removeduplicatevertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Controlla validità
        alg_params = {
            'IGNORE_RING_SELF_INTERSECTION': False,
            'INPUT_LAYER': outputs['RimuoviIVerticiDuplicati']['OUTPUT'],
            'METHOD': 2,  # GEOS
            'VALID_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ControllaValidit'] = processing.run('qgis:checkvalidity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': -1,
            'END_CAP_STYLE': 0,  # Arrotondato
            'INPUT': outputs['ControllaValidit']['VALID_OUTPUT'],
            'JOIN_STYLE': 0,  # Arrotondato
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Estrai tramite espressione
        alg_params = {
            'EXPRESSION': 'overlay_intersects(@layer)\n',
            'INPUT': outputs['Buffer']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EstraiTramiteEspressione'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Estrai per posizione
        alg_params = {
            'INPUT': outputs['ControllaValidit']['VALID_OUTPUT'],
            'INTERSECT': outputs['EstraiTramiteEspressione']['OUTPUT'],
            'PREDICATE': [2],  # disgiunto
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EstraiPerPosizione'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Controlla validità
        alg_params = {
            'IGNORE_RING_SELF_INTERSECTION': False,
            'INPUT_LAYER': outputs['EstraiPerPosizione']['OUTPUT'],
            'METHOD': 2,  # GEOS
            'VALID_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ControllaValidit'] = processing.run('qgis:checkvalidity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Controlla validità
        alg_params = {
            'IGNORE_RING_SELF_INTERSECTION': False,
            'INPUT_LAYER': outputs['ControllaValidit']['VALID_OUTPUT'],
            'METHOD': 1,  # QGIS
            'VALID_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ControllaValidit'] = processing.run('qgis:checkvalidity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Controlla validità
        alg_params = {
            'IGNORE_RING_SELF_INTERSECTION': False,
            'INPUT_LAYER': outputs['ControllaValidit']['VALID_OUTPUT'],
            'METHOD': 0,  # Selezionato nelle impostazioni di digitalizzazione
            'VALID_OUTPUT': parameters['Output']
        }
        outputs['ControllaValidit'] = processing.run('qgis:checkvalidity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Output'] = outputs['ControllaValidit']['VALID_OUTPUT']
        return results

    def name(self):
        return 'pulizia_vettore'

    def displayName(self):
        return 'pulizia_vettore'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Pulizia_vettore()
