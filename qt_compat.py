# -*- coding: utf-8 -*-
"""Small Qt5/Qt6 compatibility helpers for QGIS PyQt."""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialogButtonBox

try:
    from qgis.PyQt.QtGui import QAction  # noqa: F401
except ImportError:  # QGIS 3 / PyQt5
    from qgis.PyQt.QtWidgets import QAction  # noqa: F401


def enum_value(container, group_name, value_name):
    """Return a Qt enum value in both PyQt5 and PyQt6 style."""
    if hasattr(container, value_name):
        return getattr(container, value_name)
    group = getattr(container, group_name)
    return getattr(group, value_name)


def wait_cursor():
    return enum_value(Qt, "CursorShape", "WaitCursor")


def window_modal():
    return enum_value(Qt, "WindowModality", "WindowModal")


def rich_text():
    return enum_value(Qt, "TextFormat", "RichText")


def dialog_close_button():
    return enum_value(QDialogButtonBox, "StandardButton", "Close")
