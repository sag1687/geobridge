# -*- coding: utf-8 -*-
"""QGIS plugin entry point for VertoBridge Italia."""


def classFactory(iface):
    from .plugin import VertoBridgeItaliaPlugin

    return VertoBridgeItaliaPlugin(iface)
