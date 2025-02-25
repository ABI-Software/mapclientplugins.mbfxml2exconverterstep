
"""
MAP Client Plugin Step
"""
import logging
import os
import json

from concurrent.futures import ProcessPoolExecutor
from functools import partial

from PySide6 import QtGui, QtWidgets, QtCore

import mbfxml2ex.exceptions

from mbfxml2ex.app import read_xml
from mbfxml2ex.zinc import write_ex

from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint
from mapclientplugins.mbfxml2exconverterstep.configuredialog import ConfigureDialog

logger = logging.getLogger(__name__)


def _convert_file(file_path, output_dir):
    try:
        contents = read_xml(file_path)
    except (mbfxml2ex.exceptions.MBFXMLFormat, mbfxml2ex.exceptions.MBFXMLException):
        contents = None

    if contents is None:
        file_path_converted = f"Could not read MBF XML '{file_path}'."
        logger.warning(file_path_converted)
    else:
        split_file_name = os.path.splitext(os.path.basename(file_path))
        file_path_converted = os.path.join(output_dir, f"{split_file_name[0]}.exf")
        write_ex(file_path_converted, contents)

    return file_path_converted


def _process_files_in_parallel(file_list, output_dir):
    convert_with_output = partial(_convert_file, output_dir=output_dir)
    with ProcessPoolExecutor() as executor:
        # Map each file to the conversion function
        results = list(executor.map(convert_with_output, file_list))

    return results


class MBFXML2ExConverterStep(WorkflowStepMountPoint):

    def __init__(self, location):
        super(MBFXML2ExConverterStep, self).__init__('MBFXML2ExConverter', location)
        self._configured = False # A step cannot be executed until it has been configured.
        self._category = 'Utility'
        # Add any other initialisation code here:
        self._icon = QtGui.QImage(':/mbfxml2exconverterstep/images/utility.png')
        # Ports:
        self.addPort([('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'),
                      ('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#uses-list-of',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location')
                      ])
        self.addPort([('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'),
                      ('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#provides-list-of',
                       'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location')
                      ])
        # Port data:
        self._portData0 = None  # file_location
        self._portData1 = None  # file_location
        # Config:
        self._config = {'identifier': ''}
        self._list_input = True

    def execute(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        output_dir = os.path.join(self._location, f"output_{self._config['identifier']}")
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        self._list_input = isinstance(self._portData0, list)
        if not self._list_input:
            self._portData0 = [self._portData0]

        self._process_conversion(output_dir)

        self._doneExecution()
        QtWidgets.QApplication.restoreOverrideCursor()

    def _process_conversion(self, output_dir):
        results = _process_files_in_parallel(self._portData0, output_dir)
        converted_results = [r for r in results if not r.startswith("Could not read MBF XML")]

        self._portData1 = converted_results if self._list_input else converted_results[0] if len(converted_results) else None

    def setPortData(self, index, dataIn):
        """
        Add your code here that will set the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        uses port for this step then the index can be ignored.

        :param index: Index of the port to return.
        :param dataIn: The data to set for the port at the given index.
        """
        self._portData0 = dataIn  # file_location

    def getPortData(self, index):
        """
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.

        :param index: Index of the port to return.
        """
        return self._portData1  # file_location

    def configure(self):
        """
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        """
        dlg = ConfigureDialog(self._main_window)
        dlg.identifierOccursCount = self._identifierOccursCount
        dlg.setConfig(self._config)
        dlg.validate()
        dlg.setModal(True)

        if dlg.exec_():
            self._config = dlg.getConfig()

        self._configured = dlg.validate()
        self._configuredObserver()

    def getIdentifier(self):
        """
        The identifier is a string that must be unique within a workflow.
        """
        return self._config['identifier']

    def setIdentifier(self, identifier):
        """
        The framework will set the identifier for this step when it is loaded.
        """
        self._config['identifier'] = identifier

    def serialize(self):
        """
        Add code to serialize this step to string.  This method should
        implement the opposite of 'deserialize'.
        """
        return json.dumps(self._config, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def deserialize(self, string):
        """
        Add code to deserialize this step from string.  This method should
        implement the opposite of 'serialize'.

        :param string: JSON representation of the configuration in a string.
        """
        self._config.update(json.loads(string))

        d = ConfigureDialog()
        d.identifierOccursCount = self._identifierOccursCount
        d.setConfig(self._config)
        self._configured = d.validate()
