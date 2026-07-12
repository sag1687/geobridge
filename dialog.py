# -*- coding: utf-8 -*-
"""Main dialog for the GeoBridge QGIS plugin.

IT: finestra principale bilingue (italiano/inglese, selettore con
bandiera in alto a destra) con il tema scuro condiviso della famiglia
di plugin SinoCloud. EN: bilingual main window (Italian/English, flag
toggle at the top right) using the shared dark theme of the SinoCloud
plugin family.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from qgis.core import QgsProject, QgsVectorLayer

try:
    from qgis.core import QgsSettings
except ImportError:
    QgsSettings = None

from .layer_converter import (
    LayerConversionCancelled,
    LayerConversionError,
    convert_vector_layer,
)
from .qt_compat import (
    dialog_close_button,
    rich_text,
    wait_cursor,
    window_modal,
)
from .api_client import DEFAULT_API_URL, DEFAULT_SRS, ApiError, ApiClient
from . import plugin_hub

_SETTINGS_BASE = "GeoFusion/GeoBridge"


def _t(lang, it, en):
    """Return the Italian or English string based on lang."""
    return en if lang == "en" else it


class GeoBridgeDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self.client = ApiClient()
        self.max_coord = 32000
        self.srs_list = list(DEFAULT_SRS)
        self.srs_combos = []
        self.lang = self._load_lang()

        # Retranslation registries, consumed by _update_ui_lang().
        self._i18n_widgets = []  # (widget, setter_name, it, en)
        self._i18n_tabs = []     # (tabs_widget, index, it, en)

        self.resize(720, 560)
        self.setStyleSheet(plugin_hub.FAMILY_STYLE)
        self._build_ui()
        self._update_ui_lang()
        self.refresh_layers()
        self.load_info(silent=True)

    # ------------------------------------------------------------------
    # Language helpers
    # ------------------------------------------------------------------

    def _load_lang(self):
        if QgsSettings is not None:
            saved = QgsSettings().value(_SETTINGS_BASE + "/lang", "") or ""
            if saved in ("it", "en"):
                return saved
        return "it"

    def _save_lang(self):
        if QgsSettings is not None:
            QgsSettings().setValue(_SETTINGS_BASE + "/lang", self.lang)

    def _tr(self, widget, setter, it, en):
        self._i18n_widgets.append((widget, setter, it, en))
        return widget

    def _mklabel(self, it, en):
        lbl = QLabel()
        self._tr(lbl, "setText", it, en)
        return lbl

    def _mkbutton(self, it, en):
        btn = QPushButton()
        self._tr(btn, "setText", it, en)
        return btn

    def _mkgroup(self, it, en):
        grp = QGroupBox()
        self._tr(grp, "setTitle", it, en)
        return grp

    def _tr_tab(self, tabs, index, it, en):
        self._i18n_tabs.append((tabs, index, it, en))

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "it" else "it"
        self._save_lang()
        self._update_ui_lang()

    def _update_ui_lang(self):
        lang = self.lang
        self.setWindowTitle(_t(
            lang,
            "GeoBridge — Conversioni servizio API IGM",
            "GeoBridge — IGM API service conversions",
        ))
        self.btn_lang.setText(plugin_hub.lang_button_label(lang))
        for widget, setter, it, en in self._i18n_widgets:
            getattr(widget, setter)(_t(lang, it, en))
        for tabs, index, it, en in self._i18n_tabs:
            tabs.setTabText(index, _t(lang, it, en))
        if hasattr(self, "family_widget"):
            self.family_widget.set_lang(lang)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        title = QLabel("🌉 GeoBridge")
        title.setStyleSheet(
            "color:#5b9bd5; font-size:15px; font-weight:700;"
        )
        top_bar.addWidget(title)
        top_bar.addStretch(1)
        self.btn_lang = QPushButton(plugin_hub.LANG_LABEL_EN)
        self.btn_lang.setObjectName("btnLang")
        self.btn_lang.clicked.connect(self._toggle_lang)
        top_bar.addWidget(self.btn_lang)
        layout.addLayout(top_bar)

        intro = self._mklabel(
            "Client QGIS non ufficiale per le API servizio API IGM "
            "dell'Istituto Geografico Militare. "
            "Conversione planimetrica; quote non trasformate.",
            "Unofficial QGIS client for the IGM API service of the "
            "Italian Military Geographic Institute. Planimetric "
            "conversion; heights are not transformed.",
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.tabs = QTabWidget()
        idx = self.tabs.addTab(self._coordinate_tab(), "")
        self._tr_tab(self.tabs, idx, "Coordinate", "Coordinates")
        idx = self.tabs.addTab(self._layer_tab(), "")
        self._tr_tab(self.tabs, idx, "Layer vettoriale", "Vector layer")
        self.tabs.addTab(self._notice_tab(), "ℹ Info")
        layout.addWidget(self.tabs)

        buttons = QDialogButtonBox(dialog_close_button())
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _coordinate_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form_group = self._mkgroup(
            "Conversione singola", "Single conversion"
        )
        form = QFormLayout(form_group)
        self.coord_in_combo = self._new_srs_combo()
        self.coord_out_combo = self._new_srs_combo()
        self.coord_e_edit = QLineEdit()
        self.coord_n_edit = QLineEdit()
        self._tr(
            self.coord_e_edit, "setPlaceholderText",
            "Est / longitudine", "Easting / longitude",
        )
        self._tr(
            self.coord_n_edit, "setPlaceholderText",
            "Nord / latitudine", "Northing / latitude",
        )
        self.coord_result_e = QLineEdit()
        self.coord_result_n = QLineEdit()
        self.coord_result_e.setReadOnly(True)
        self.coord_result_n.setReadOnly(True)

        form.addRow(
            self._mklabel("Da CRS", "From CRS"), self.coord_in_combo
        )
        form.addRow(
            self._mklabel("A CRS", "To CRS"), self.coord_out_combo
        )
        form.addRow("E / lon", self.coord_e_edit)
        form.addRow("N / lat", self.coord_n_edit)
        form.addRow(
            self._mklabel("E convertita", "Converted E"),
            self.coord_result_e,
        )
        form.addRow(
            self._mklabel("N convertita", "Converted N"),
            self.coord_result_n,
        )
        layout.addWidget(form_group)

        row = QHBoxLayout()
        self.coord_convert_btn = self._mkbutton(
            "Converti coordinata", "Convert coordinate"
        )
        self.coord_convert_btn.clicked.connect(self.convert_coordinate)
        self.coord_swap_btn = self._mkbutton("Inverti CRS", "Swap CRS")
        self.coord_swap_btn.clicked.connect(
            lambda: self._swap_combos(
                self.coord_in_combo, self.coord_out_combo
            )
        )
        row.addWidget(self.coord_convert_btn)
        row.addWidget(self.coord_swap_btn)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)
        return tab

    def _layer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = self._mkgroup("Conversione layer", "Layer conversion")
        grid = QGridLayout(group)
        self.layer_combo = QComboBox()
        self.layer_refresh_btn = self._mkbutton("Aggiorna", "Refresh")
        self.layer_refresh_btn.clicked.connect(self.refresh_layers)
        self.layer_in_combo = self._new_srs_combo()
        self.layer_out_combo = self._new_srs_combo()
        self.selected_only_check = QCheckBox()
        self._tr(
            self.selected_only_check, "setText",
            "Solo feature selezionate", "Selected features only",
        )
        self.output_name_edit = QLineEdit()
        self._tr(
            self.output_name_edit, "setPlaceholderText",
            "Nome layer temporaneo", "Temporary layer name",
        )
        self.layer_convert_btn = self._mkbutton(
            "Converti layer", "Convert layer"
        )
        self.layer_convert_btn.clicked.connect(self.convert_layer)
        self.layer_status_label = QLabel("")
        self.layer_status_label.setWordWrap(True)

        grid.addWidget(QLabel("Layer"), 0, 0)
        grid.addWidget(self.layer_combo, 0, 1)
        grid.addWidget(self.layer_refresh_btn, 0, 2)
        grid.addWidget(self._mklabel("Da CRS", "From CRS"), 1, 0)
        grid.addWidget(self.layer_in_combo, 1, 1, 1, 2)
        grid.addWidget(self._mklabel("A CRS", "To CRS"), 2, 0)
        grid.addWidget(self.layer_out_combo, 2, 1, 1, 2)
        grid.addWidget(QLabel("Output"), 3, 0)
        grid.addWidget(self.output_name_edit, 3, 1, 1, 2)
        grid.addWidget(self.selected_only_check, 4, 1, 1, 2)
        grid.addWidget(self.layer_convert_btn, 5, 1)
        grid.addWidget(self.layer_status_label, 6, 0, 1, 3)
        layout.addWidget(group)

        info = self._mklabel(
            "Il plugin crea un layer temporaneo e copia gli attributi. "
            "Tutti i vertici XY sono inviati al servizio API IGM in "
            "blocchi.",
            "The plugin creates a temporary layer and copies the "
            "attributes. All XY vertices are sent to the IGM API "
            "service in blocks.",
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch(1)
        self.layer_combo.currentIndexChanged.connect(
            self._sync_layer_defaults
        )
        return tab

    def _notice_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        details = QLabel()
        details.setObjectName("infoDetails")
        details.setTextFormat(rich_text())
        details.setWordWrap(True)
        self._tr(
            details, "setText",
            "<b>Autore client:</b> Dott. Sarino Alfonso Grande<br/>"
            "<b>Email:</b> sino.grande@gmail.com &mdash; "
            "<b>Sito:</b> <a href='https://sinocloud.it'>"
            "sinocloud.it</a><br/>"
            "<b>Licenza client:</b> GPL-2.0-or-later<br/>"
            "<b>Servizio API:</b> servizio API IGM, "
            "Istituto Geografico Militare<br/>"
            "<b>Relazione con IGM:</b> client non ufficiale, "
            "non approvato o certificato da IGM",
            "<b>Client author:</b> Dott. Sarino Alfonso Grande<br/>"
            "<b>Email:</b> sino.grande@gmail.com &mdash; "
            "<b>Website:</b> <a href='https://sinocloud.it'>"
            "sinocloud.it</a><br/>"
            "<b>Client license:</b> GPL-2.0-or-later<br/>"
            "<b>API service:</b> IGM API service, Italian Military "
            "Geographic Institute<br/>"
            "<b>Relationship with IGM:</b> unofficial client, not "
            "approved or certified by IGM",
        )
        details.setOpenExternalLinks(True)
        layout.addWidget(details)

        text = QTextBrowser()
        text.setObjectName("noticeText")
        text.setOpenExternalLinks(True)
        text.setHtml(_notice_html())
        layout.addWidget(text, 1)

        self.family_widget = plugin_hub.make_family_widget(
            "geobridge", lang=self.lang
        )
        layout.addWidget(self.family_widget)

        row = QHBoxLayout()
        api_btn = self._mkbutton("Pagina IGM", "IGM page")
        api_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(
                    "https://igmi.esercito.difesa.it/servizi/"
                    "verto-online/"
                )
            )
        )
        endpoint_btn = self._mkbutton("Endpoint API", "API endpoint")
        endpoint_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DEFAULT_API_URL))
        )
        row.addWidget(api_btn)
        row.addWidget(endpoint_btn)
        row.addStretch(1)
        layout.addLayout(row)
        return tab

    def _new_srs_combo(self):
        combo = QComboBox()
        combo.setMinimumWidth(360)
        self.srs_combos.append(combo)
        return combo

    # ------------------------------------------------------------------
    # API info / SRS lists
    # ------------------------------------------------------------------

    def load_info(self, silent=False):
        try:
            QApplication.setOverrideCursor(wait_cursor())
            info = self.client.info()
            self.max_coord = int(info["maxCoord"])
            self.srs_list = info["srsSupportati"]
            self._populate_srs_combos()
            self.layer_status_label.setText(_t(
                self.lang,
                "API servizio API IGM raggiunta. Massimo coordinate "
                "per richiesta: %s." % self.max_coord,
                "IGM API service reached. Maximum coordinates per "
                "request: %s." % self.max_coord,
            ))
        except (ApiError, ValueError) as exc:
            self.srs_list = list(DEFAULT_SRS)
            self._populate_srs_combos()
            self.layer_status_label.setText(_t(
                self.lang,
                "API non raggiungibile ora: uso elenco EPSG locale. "
                "Dettaglio: %s" % exc,
                "API unreachable right now: using the local EPSG "
                "list. Detail: %s" % exc,
            ))
            if not silent:
                QMessageBox.warning(self, "servizio API IGM", str(exc))
        finally:
            QApplication.restoreOverrideCursor()

    def _populate_srs_combos(self):
        for combo in self.srs_combos:
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for item in self.srs_list:
                combo.addItem(
                    "EPSG:%s - %s" % (item["epsg"], item["descrizione"]),
                    item["epsg"],
                )
            combo.blockSignals(False)
            self._set_combo_epsg(combo, current or 6706)
        self._sync_layer_defaults()

    def refresh_layers(self):
        current = (
            self.layer_combo.currentData()
            if hasattr(self, "layer_combo") else None
        )
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                self.layer_combo.addItem(layer.name(), layer.id())
        self.layer_combo.blockSignals(False)
        if current:
            index = self.layer_combo.findData(current)
            if index >= 0:
                self.layer_combo.setCurrentIndex(index)
        self._sync_layer_defaults()

    def _sync_layer_defaults(self):
        layer = self._current_layer()
        if not layer:
            return
        epsg = layer.crs().postgisSrid()
        if epsg:
            self._set_combo_epsg(self.layer_in_combo, epsg)
        if not self.output_name_edit.text().strip():
            self.output_name_edit.setText(
                "%s - GeoBridge" % layer.name()
            )

    # ------------------------------------------------------------------
    # Conversions
    # ------------------------------------------------------------------

    def convert_coordinate(self):
        try:
            e = _parse_float(
                self.coord_e_edit.text(), "E / lon", self.lang
            )
            n = _parse_float(
                self.coord_n_edit.text(), "N / lat", self.lang
            )
            in_epsg = self._combo_epsg(self.coord_in_combo)
            out_epsg = self._combo_epsg(self.coord_out_combo)
            QApplication.setOverrideCursor(wait_cursor())
            converted = self.client.convert(
                in_epsg, out_epsg, [{"e": e, "n": n}]
            )[0]
            self.coord_result_e.setText("%.12f" % converted["e"])
            self.coord_result_n.setText("%.12f" % converted["n"])
        except (ValueError, ApiError) as exc:
            QMessageBox.warning(
                self,
                _t(self.lang, "Conversione coordinata",
                   "Coordinate conversion"),
                str(exc),
            )
        finally:
            QApplication.restoreOverrideCursor()

    def convert_layer(self):
        layer = self._current_layer()
        if not layer:
            QMessageBox.warning(
                self,
                _t(self.lang, "Conversione layer", "Layer conversion"),
                _t(self.lang,
                   "Seleziona un layer vettoriale valido.",
                   "Select a valid vector layer."),
            )
            return

        in_epsg = self._combo_epsg(self.layer_in_combo)
        out_epsg = self._combo_epsg(self.layer_out_combo)
        output_name = self.output_name_edit.text().strip()
        if not output_name:
            output_name = "%s - GeoBridge" % layer.name()
        progress = QProgressDialog(
            _t(self.lang,
               "Preparazione conversione servizio API IGM",
               "Preparing IGM API service conversion"),
            _t(self.lang, "Annulla", "Cancel"),
            0,
            0,
            self,
        )
        progress.setWindowModality(window_modal())
        progress.show()

        def update_progress(message, value, total):
            progress.setLabelText(message)
            if total:
                progress.setMaximum(total)
                progress.setValue(value)
            QApplication.processEvents()

        try:
            QApplication.setOverrideCursor(wait_cursor())
            output_layer = convert_vector_layer(
                layer,
                self.client,
                in_epsg,
                out_epsg,
                selected_only=self.selected_only_check.isChecked(),
                output_name=output_name,
                max_per_request=self.max_coord,
                progress=update_progress,
                cancel_requested=progress.wasCanceled,
            )
            QgsProject.instance().addMapLayer(output_layer)
            self.layer_status_label.setText(_t(
                self.lang,
                "Creato layer: %s" % output_layer.name(),
                "Layer created: %s" % output_layer.name(),
            ))
            QMessageBox.information(
                self,
                _t(self.lang, "Conversione completata",
                   "Conversion complete"),
                _t(self.lang,
                   "Layer creato: %s" % output_layer.name(),
                   "Layer created: %s" % output_layer.name()),
            )
        except LayerConversionCancelled:
            self.layer_status_label.setText(_t(
                self.lang,
                "Conversione annullata.",
                "Conversion cancelled.",
            ))
        except (LayerConversionError, ApiError, StopIteration) as exc:
            QMessageBox.warning(
                self,
                _t(self.lang, "Conversione layer", "Layer conversion"),
                str(exc),
            )
        finally:
            QApplication.restoreOverrideCursor()
            progress.close()

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def _current_layer(self):
        layer_id = self.layer_combo.currentData()
        if not layer_id:
            return None
        layer = QgsProject.instance().mapLayer(layer_id)
        return layer if isinstance(layer, QgsVectorLayer) else None

    def _combo_epsg(self, combo):
        return int(combo.currentData())

    def _set_combo_epsg(self, combo, epsg):
        if not epsg:
            return
        index = combo.findData(int(epsg))
        if index >= 0:
            combo.setCurrentIndex(index)

    def _swap_combos(self, first, second):
        first_epsg = self._combo_epsg(first)
        second_epsg = self._combo_epsg(second)
        self._set_combo_epsg(first, second_epsg)
        self._set_combo_epsg(second, first_epsg)


def _parse_float(value, label, lang="it"):
    text = value.strip().replace(",", ".")
    if not text:
        raise ValueError(_t(
            lang,
            "Valore mancante: %s" % label,
            "Missing value: %s" % label,
        ))
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(_t(
            lang,
            "Valore numerico non valido per %s" % label,
            "Invalid numeric value for %s" % label,
        )) from exc


def _notice_html():
    return """
    <style>
      body { color: #c3ccd6; background: #1b2430; }
      h3 { color: #5b9bd5; }
      a { color: #5b9bd5; }
      b { color: #f2f5f8; }
    </style>
    <h3>Informativa IGM e licenza / IGM notice and license</h3>
    <p><b>IT:</b> GeoBridge &egrave; un client QGIS non ufficiale,
    indipendente e non sviluppato, approvato, certificato, distribuito
    o garantito dall'Istituto Geografico Militare. Il servizio usato
    &egrave; l'API IGM dell'Istituto Geografico Militare
    (<a href="https://igmi.esercito.difesa.it/servizi/verto-online/">
    fonte ufficiale</a>). Il servizio, il software sottostante,
    l'infrastruttura, le denominazioni istituzionali, le API e
    l'implementazione restano di titolarit&agrave; dell'Istituto
    Geografico Militare: il plugin non trasferisce, concede o
    rivendica alcun diritto su tali elementi. Il client invia
    all'endpoint pubblico IGM le coordinate necessarie alla
    conversione: non usare il plugin per dati che non possono essere
    trasmessi a servizi esterni secondo le regole del proprio ente,
    contratto o incarico. L'uso &egrave; subordinato alle condizioni
    pubblicate da IGM; le API possono essere modificate, limitate,
    sospese o interrotte da IGM. Salvo diversa indicazione ufficiale,
    i risultati mantengono la licenza e i vincoli dei dati in
    ingresso; il plugin non fornisce certificazione ufficiale IGM dei
    risultati.</p>
    <p><b>EN:</b> GeoBridge is an unofficial, independent QGIS client,
    not developed, approved, certified, distributed or guaranteed by
    the Italian Military Geographic Institute (IGM). The service used
    is the IGM API
    (<a href="https://igmi.esercito.difesa.it/servizi/verto-online/">
    official source</a>). The service, the underlying software, the
    infrastructure, the institutional names, the APIs and their
    implementation remain the property of the IGM: the plugin does
    not transfer, grant or claim any right over them. The client
    sends the coordinates needed for the conversion to the public IGM
    endpoint: do not use the plugin for data that cannot be sent to
    external services under your organisation's rules, contract or
    assignment. Use is subject to the conditions published by IGM;
    the APIs may be changed, limited, suspended or discontinued by
    IGM. Unless officially stated otherwise, results keep the license
    and constraints of the input data; the plugin provides no
    official IGM certification of the results.</p>
    <p><b>Endpoint API:</b> __API_URL__</p>
    <p><b>Codice plugin / Plugin code:</b> GPL-2.0-or-later. Vedere /
    See LICENSE, NOTICE.md, LEGAL_IGM_PUBLICATION_REVIEW.md.</p>
    """.replace("__API_URL__", DEFAULT_API_URL)
