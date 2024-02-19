# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HamburgSuche
                                 A QGIS plugin
 Sucht Straßennamen
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-10-14
        git sha              : $Format:%H$
        copyright            : (C) 2020 by LGV Hamburg
        email                : florian.timm@gv.hamburg.de
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QTimer
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem
from qgis.PyQt.QtWidgets import QCompleter, QAction
# Initialize Qt resources from file resources.py
from .resources import *
from qgis.core import Qgis, QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

from xml.etree import ElementTree

# Import the code for the DockWidget
from .HamburgSuche_dockwidget import HamburgSucheDockWidget
import os.path
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.PyQt.QtCore import QSettings, QUrl


class HamburgSuche:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'HamburgSuche_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []

        self.networkManager = QNetworkAccessManager()
        self.networkManager.finished.connect(self.handleResult)

        # print "** STARTING HamburgSuche"

        self.dockwidget = HamburgSucheDockWidget()

        self.dockwidget.closingPlugin.connect(self.onClosePlugin)

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.dockwidget.show()

        self.completer = QCompleter(["Suche..."])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        # self.completer.setWrapAround(False)
        # self.completer.setWidget(self.dockwidget.searchBar)

        self.completer.highlighted.connect(self.doneCompletion)
        self.completer.activated.connect(self.onActivated)

        self.dockwidget.searchBar.returnPressed.connect(self.suche)
        self.dockwidget.searchBar.textChanged.connect(self.suche)
        self.dockwidget.searchBar.setCompleter(self.completer)

        self.treffer = False

        if QgsCoordinateReferenceSystem is not None:
            srcCrs = QgsCoordinateReferenceSystem("EPSG:25832")
            dstCrs = iface.mapCanvas().mapSettings().destinationCrs()
            self.crsTransform = QgsCoordinateTransform(
                srcCrs, dstCrs, QgsProject.instance())

    # noinspection PyMethodMayBeStatic

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
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING HamburgSuche"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD HamburgSuche"

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

    def suche(self):
        """Sucht..."""

        if len(self.dockwidget.searchBar.text()) < 3:
            return

        if self.treffer:
            self.treffer = False
            return

        # self.iface.messageBar().pushMessage('Suche: {}'.format(
        #    self.dockwidget.searchBar.text()), Qgis.Info)

        qurl = "https://geoportal-hamburg.de/geodienste_hamburg_de/HH_WFS_DOG?service=WFS&request=GetFeature&version=2.0.0&StoredQuery_ID=findeStrasse&strassenname=" + \
            self.dockwidget.searchBar.text()

        self.networkManager.get(QNetworkRequest(QUrl(qurl)))

    def handleResult(self, result):

        # print "received url:", url.toString()
        if result.error():
            return

        response = result.readAll()
        pystring = str(response, 'utf-8')
        tree = ElementTree.fromstring(pystring)
        liste = tree.findall('wfs:member', namespaces={
            'wfs': 'http://www.opengis.net/wfs/2.0'})
        if len(liste) == 0:
            self.iface.messageBar().pushMessage('Kein Treffer: {}'.format(
                self.dockwidget.searchBar.text()), Qgis.Info)
            return
        model = QStandardItemModel()
        for eintrag in liste:
            strasse = eintrag.find('dog:Strassen', namespaces={
                'dog': "http://www.adv-online.de/namespaces/adv/dog"})
            sname = strasse.find('dog:strassenname', namespaces={
                'dog': "http://www.adv-online.de/namespaces/adv/dog"})

            coord = strasse.find('iso19112:position_strassenachse', namespaces={'iso19112': 'http://www.opengis.net/iso19112'}).find('gml:Point', namespaces={
                'gml': "http://www.opengis.net/gml/3.2"}).find('gml:pos', namespaces={'gml': "http://www.opengis.net/gml/3.2"}).text.split(' ')

            item = QStandardItem(sname.text)
            item.setData(coord, Qt.UserRole+1)
            model.appendRow(item)
        result.deleteLater()
        self.completer.setModel(model)
        self.completer.complete()

    def doneCompletion(self, text):
        # self.iface.messageBar().pushMessage('Something selected' + text, Qgis.Info)
        items = self.completer.model().findItems(text)
        if len(items) > 0:
            item = items[0]
            coord = item.data(Qt.UserRole+1)
            # self.iface.messageBar().pushMessage(
            #    self.tr('Suche: {}').format(coord), Qgis.Info)

            geom = QgsGeometry.fromPointXY(
                QgsPointXY(float(coord[0]), float(coord[1])))

            # Zoom to feature
            bufgeom = geom.buffer(200.0, 2)
            bufgeom.transform(self.crsTransform)
            rect = bufgeom.boundingBox()
            canvas = self.iface.mapCanvas()
            canvas.setExtent(rect)

            # geom.transform(self.crsTransform)
            # self.setMarkerGeom(geom)

            canvas.refresh()
            self.completer.popup().hide()
            self.treffer = True

    def onActivated(self):
        QTimer.singleShot(0, self.dockwidget.searchBar.clear)
