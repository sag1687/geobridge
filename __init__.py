# -*- coding: utf-8 -*-
"""QGIS plugin entry point for GeoBridge."""


def classFactory(iface):
    from .plugin import GeoBridgePlugin

    return GeoBridgePlugin(iface)
