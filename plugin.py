# -*- coding: utf-8 -*-
"""QGIS plugin bootstrap for GeoBridge."""

from __future__ import annotations

import os

from qgis.PyQt.QtGui import QIcon

from .dialog import GeoBridgeDialog
from .qt_compat import QAction


class GeoBridgePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.menu_name = "&GeoBridge"

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.svg")
        self.action = QAction(
            QIcon(icon_path), "GeoBridge", self.iface.mainWindow()
        )
        self.action.setObjectName("geobridge_action")
        self.action.setToolTip(
            "Client QGIS non ufficiale per conversioni tramite "
            "API servizio API IGM / Unofficial QGIS client for "
            "conversions through the IGM API service"
        )
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu(self.menu_name, self.action)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginVectorMenu(self.menu_name, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        self.dialog = None

    def run(self):
        self.dialog = GeoBridgeDialog(self.iface)
        if hasattr(self.dialog, "exec"):
            self.dialog.exec()
        else:
            self.dialog.exec_()
