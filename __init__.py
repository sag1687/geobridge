# -*- coding: utf-8 -*-
"""QGIS plugin entry point for GeoBridgeIT."""


def classFactory(iface):
    from .plugin import GeoBridgeITPlugin

    return GeoBridgeITPlugin(iface)
