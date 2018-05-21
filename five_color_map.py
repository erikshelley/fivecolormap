# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FiveColorMap
                                 A QGIS plugin
 This plugin colors each shape differently than its neighbors using five colors
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-05-20
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Erik Shelley
        email                : erik@erikshelley.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
#from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QObject
#from PyQt5.QtGui import QIcon
#from PyQt5.QtWidgets import QAction, QFileDialog, QProgressBar
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .five_color_map_dialog import FiveColorMapDialog
import os.path

from qgis.core import QgsProject, QgsMapLayer, QgsWkbTypes, Qgis, QgsMessageLog, QgsGeometry
from qgis.gui import QgsMessageBar

import traceback, sys


class FiveColorMap:
    """QGIS Plugin Implementation."""

    #def __init__(self, iface):
    def __init__(self, *args, **kwargs):
        super(FiveColorMap, self).__init__()
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        #self.iface = iface
        self.iface = args[0]

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FiveColorMap_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = FiveColorMapDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&FiveColorMap')

        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'FiveColorMap')
        self.toolbar.setObjectName(u'FiveColorMap')

        #self.dlg.lineEdit.clear()
        #self.dlg.pushButton.clicked.connect(self.select_output_file)
        self.dlg.comboBoxLayer.currentIndexChanged.connect(self.layer_changed)
        self.dlg.comboBoxField.currentIndexChanged.connect(self.field_changed)
        self.threadpool = QThreadPool()


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('FiveColorMap', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/five_color_map/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Five Color Map'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&FiveColorMap'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def layer_changed(self):
        self.dlg.comboBoxField.clear()
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        self.selectedLayer = self.vpLayers[selectedLayerIndex]
        #self.iface.messageBar().pushMessage("Layer Selected", self.selectedLayer.name(), level=Qgis.Info, duration=1)
        QgsMessageLog.logMessage("Layer Selected: " + self.selectedLayer.name(), level=Qgis.Info)
        fields = self.selectedLayer.fields()
        self.fieldNameList = [field.name() for field in fields]
        self.dlg.comboBoxField.addItems(self.fieldNameList)


    def field_changed(self):
        self.selectedFieldText = self.dlg.comboBoxField.itemText(self.dlg.comboBoxField.currentIndex()) 
        if self.dlg.comboBoxField.currentIndex() > -1: 
            #self.iface.messageBar().pushMessage("Field Selected", self.selectedFieldText, level=Qgis.Info, duration=1)
            QgsMessageLog.logMessage("Field Selected: " + self.selectedFieldText, level=Qgis.Info)


    def show_progress(self, value):
        self.progressBar.setValue(value)

        
    def finished_graph(self, message):
        QgsMessageLog.logMessage(message, level=Qgis.Info)


    def finished_thread(self):
        self.iface.messageBar().clearWidgets()


    #def create_graph(self, progress_callback):
    def create_graph(self, progress_callback):
        polygons = [QgsGeometry(feature.geometry()) for feature in self.selectedLayer.getFeatures()]
        featureCount = self.selectedLayer.featureCount()
        graph = [set() for i in range(featureCount)]
        for i in range(featureCount - 1):
            #progressBar.setValue(i + 1)
            progress_callback.emit(i + 1)
            for j in range(i + 1, featureCount):
                if polygons[i].touches(polygons[j]):
                    intersection = polygons[i].intersection(polygons[j])
                    if intersection is not None and intersection.type() in [1, 2]:
                        graph[i].add(j)
                        graph[j].add(i)
            QgsMessageLog.logMessage("Feature: " + str(i), level=Qgis.Info)
        return "Graph completed."


        
    def run(self):
        """Run method that performs all the real work"""

        # Fill input layer ComboBox
        self.dlg.comboBoxLayer.clear()
        allLayers = QgsProject.instance().mapLayers()
        self.vpLayers = []
        for (id, layer) in list(allLayers.items()):
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.vpLayers.append(layer);
                self.dlg.comboBoxLayer.addItem(layer.name(), layer.id())

        # Pre-select active layer
        activeLayer = self.iface.activeLayer()
        if activeLayer:
            if activeLayer.type() == QgsMapLayer.VectorLayer and activeLayer.geometryType() == QgsWkbTypes.PolygonGeometry:
                index = self.dlg.comboBoxLayer.findData(activeLayer.id())
                self.dlg.comboBoxLayer.setCurrentIndex(index)

        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            progressMessageBar = self.iface.messageBar().createMessage("Creating graph from polygons...")
            self.progressBar = QProgressBar()
            self.progressBar.setMaximum(self.selectedLayer.featureCount())
            self.progressBar.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(self.progressBar)
            self.iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

            # Pass the function to execute
            worker = Worker(self.create_graph)
            worker.signals.result.connect(self.finished_graph)
            worker.signals.finished.connect(self.finished_thread)
            worker.signals.progress.connect(self.show_progress)

            # Execute
            self.threadpool.start(worker)

            #featureList = self.selectedLayer.getFeatures()
            #for feature in featureList:
            #    QgsMessageLog.logMessage("Feature: " + str(feature.id()), level=Qgis.Info)
            #self.selectedLayer.startEditing()
            #self.selectedLayer.changeAttributeValue(0, self.fieldNameList.index(self.selectedFieldText), 1)
            #self.selectedLayer.commitChanges()


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
