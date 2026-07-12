# -*- coding: utf-8 -*-
"""Conversion helpers for QGIS vector layers using servizio API IGM."""

from __future__ import annotations

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsVectorLayer,
    QgsWkbTypes,
)


class LayerConversionError(RuntimeError):
    pass


class LayerConversionCancelled(LayerConversionError):
    pass


def convert_vector_layer(
    source_layer,
    client,
    in_epsg,
    out_epsg,
    selected_only=False,
    output_name=None,
    max_per_request=32000,
    progress=None,
    cancel_requested=None,
):
    """Convert every vertex of a vector layer through the API IGM.

    Returns a memory layer with copied attributes and transformed geometries.
    The service is planimetric: Z/M values, if present, are left unchanged by
    QGIS geometry copying while X/Y are replaced with GeoBridge results.
    """

    if not source_layer or not source_layer.isValid():
        raise LayerConversionError("Layer sorgente non valido")

    features = list(
        source_layer.selectedFeatures()
        if selected_only
        else source_layer.getFeatures()
    )
    if not features:
        raise LayerConversionError("Nessuna feature da convertire")

    geometries = []
    all_coords = []
    for index, feature in enumerate(features, start=1):
        if cancel_requested and cancel_requested():
            raise LayerConversionCancelled("Conversione annullata")
        geometry = QgsGeometry(feature.geometry())
        geometries.append(geometry)
        if geometry.isNull() or geometry.isEmpty():
            continue
        for vertex in geometry.vertices():
            all_coords.append({"e": vertex.x(), "n": vertex.y()})
        if progress:
            progress(
                "Lettura geometrie: feature %s di %s" % (index, len(features)),
                0,
                0,
            )

    if not all_coords:
        raise LayerConversionError(
            "Le feature non contengono vertici convertibili"
        )

    converted_coords = client.convert_many(
        in_epsg,
        out_epsg,
        all_coords,
        max_per_request=max_per_request,
        progress=progress,
    )
    coord_iter = iter(converted_coords)

    output_layer = _make_memory_layer(
        source_layer,
        int(out_epsg),
        output_name
        or "%s - GeoBridge EPSG:%s" % (source_layer.name(), out_epsg),
    )
    provider = output_layer.dataProvider()
    provider.addAttributes(
        [
            source_layer.fields().at(i)
            for i in range(source_layer.fields().count())
        ]
    )
    output_layer.updateFields()
    output_fields = output_layer.fields()

    output_features = []
    for index, (source_feature, geometry) in enumerate(
        zip(features, geometries), start=1
    ):
        if cancel_requested and cancel_requested():
            raise LayerConversionCancelled("Conversione annullata")
        if not geometry.isNull() and not geometry.isEmpty():
            _transform_geometry_xy(geometry, coord_iter)

        output_feature = QgsFeature(output_fields)
        output_feature.setAttributes(source_feature.attributes())
        output_feature.setGeometry(geometry)
        output_features.append(output_feature)
        if progress:
            progress(
                "Creazione layer convertito: feature %s di %s"
                % (index, len(features)),
                index,
                len(features),
            )

    ok, _ = provider.addFeatures(output_features)
    if not ok:
        raise LayerConversionError(
            "Impossibile scrivere le feature nel layer temporaneo"
        )
    output_layer.updateExtents()
    return output_layer


def _make_memory_layer(source_layer, out_epsg, name):
    wkb_name = QgsWkbTypes.displayString(source_layer.wkbType())
    if not wkb_name or wkb_name.lower() == "unknown":
        wkb_name = QgsWkbTypes.geometryDisplayString(
            source_layer.geometryType()
        )
    crs = QgsCoordinateReferenceSystem("EPSG:%s" % out_epsg)
    layer = QgsVectorLayer(
        "%s?crs=%s"
        % (wkb_name, crs.authid() or "EPSG:%s" % out_epsg),
        name,
        "memory",
    )
    if not layer.isValid():
        raise LayerConversionError(
            "Impossibile creare il layer temporaneo di output"
        )
    return layer


def _replace_xy(point, coord):
    try:
        new_point = QgsPoint(point)
        new_point.setX(float(coord["e"]))
        new_point.setY(float(coord["n"]))
        return new_point
    except TypeError:
        return QgsPoint(float(coord["e"]), float(coord["n"]))


def _transform_geometry_xy(geometry, coord_iter):
    if hasattr(geometry, "transformVertices"):
        geometry.transformVertices(
            lambda point: _replace_xy(point, next(coord_iter))
        )
        return

    vertex_count = sum(1 for _ in geometry.vertices())
    for vertex_index in range(vertex_count):
        coord = next(coord_iter)
        moved = geometry.moveVertex(
            float(coord["e"]), float(coord["n"]), vertex_index
        )
        if not moved:
            raise LayerConversionError(
                "Impossibile aggiornare il vertice %s" % vertex_index
            )
