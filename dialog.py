# -*- coding: utf-8 -*-
"""Main dialog for the GeoBridgeIT QGIS plugin."""

from __future__ import annotations

import os

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
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

from .layer_converter import (
    LayerConversionCancelled,
    LayerConversionError,
    convert_vector_layer,
)
from .qt_compat import dialog_close_button, rich_text, wait_cursor, window_modal
from .api_client import DEFAULT_API_URL, DEFAULT_SRS, ApiError, ApiClient


class GeoBridgeDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self.client = ApiClient()
        self.max_coord = 32000
        self.srs_list = list(DEFAULT_SRS)
        self.srs_combos = []

        self.setWindowTitle("GeoBridgeIT")
        self.resize(720, 520)
        self._apply_cyber_mint_theme()
        self._build_ui()
        self.refresh_layers()
        self.load_info(silent=True)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Client QGIS non ufficiale per le API servizio API IGM dell'Istituto Geografico Militare. "
            "Conversione planimetrica; quote non trasformate."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._coordinate_tab(), "Coordinate")
        self.tabs.addTab(self._layer_tab(), "Layer vettoriale")
        self.tabs.addTab(self._notice_tab(), "Info")
        layout.addWidget(self.tabs)

        buttons = QDialogButtonBox(dialog_close_button())
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _coordinate_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form_group = QGroupBox("Conversione singola")
        form = QFormLayout(form_group)
        self.coord_in_combo = self._new_srs_combo()
        self.coord_out_combo = self._new_srs_combo()
        self.coord_e_edit = QLineEdit()
        self.coord_n_edit = QLineEdit()
        self.coord_e_edit.setPlaceholderText("Est / longitudine")
        self.coord_n_edit.setPlaceholderText("Nord / latitudine")
        self.coord_result_e = QLineEdit()
        self.coord_result_n = QLineEdit()
        self.coord_result_e.setReadOnly(True)
        self.coord_result_n.setReadOnly(True)

        form.addRow("Da CRS", self.coord_in_combo)
        form.addRow("A CRS", self.coord_out_combo)
        form.addRow("E / lon", self.coord_e_edit)
        form.addRow("N / lat", self.coord_n_edit)
        form.addRow("E convertita", self.coord_result_e)
        form.addRow("N convertita", self.coord_result_n)
        layout.addWidget(form_group)

        row = QHBoxLayout()
        self.coord_convert_btn = QPushButton("Converti coordinata")
        self.coord_convert_btn.clicked.connect(self.convert_coordinate)
        self.coord_swap_btn = QPushButton("Inverti CRS")
        self.coord_swap_btn.clicked.connect(
            lambda: self._swap_combos(self.coord_in_combo, self.coord_out_combo)
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

        group = QGroupBox("Conversione layer")
        grid = QGridLayout(group)
        self.layer_combo = QComboBox()
        self.layer_refresh_btn = QPushButton("Aggiorna")
        self.layer_refresh_btn.clicked.connect(self.refresh_layers)
        self.layer_in_combo = self._new_srs_combo()
        self.layer_out_combo = self._new_srs_combo()
        self.selected_only_check = QCheckBox("Solo feature selezionate")
        self.output_name_edit = QLineEdit()
        self.output_name_edit.setPlaceholderText("Nome layer temporaneo")
        self.layer_convert_btn = QPushButton("Converti layer")
        self.layer_convert_btn.clicked.connect(self.convert_layer)
        self.layer_status_label = QLabel("")
        self.layer_status_label.setWordWrap(True)

        grid.addWidget(QLabel("Layer"), 0, 0)
        grid.addWidget(self.layer_combo, 0, 1)
        grid.addWidget(self.layer_refresh_btn, 0, 2)
        grid.addWidget(QLabel("Da CRS"), 1, 0)
        grid.addWidget(self.layer_in_combo, 1, 1, 1, 2)
        grid.addWidget(QLabel("A CRS"), 2, 0)
        grid.addWidget(self.layer_out_combo, 2, 1, 1, 2)
        grid.addWidget(QLabel("Output"), 3, 0)
        grid.addWidget(self.output_name_edit, 3, 1, 1, 2)
        grid.addWidget(self.selected_only_check, 4, 1, 1, 2)
        grid.addWidget(self.layer_convert_btn, 5, 1)
        grid.addWidget(self.layer_status_label, 6, 0, 1, 3)
        layout.addWidget(group)

        info = QLabel(
            "Il plugin crea un layer temporaneo e copia gli attributi. "
            "Tutti i vertici XY sono inviati al servizio servizio API IGM in blocchi."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch(1)
        self.layer_combo.currentIndexChanged.connect(self._sync_layer_defaults)
        return tab

    def _notice_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("GeoBridgeIT")
        title.setObjectName("infoTitle")
        layout.addWidget(title)

        details = QLabel(
            "<b>Autore client:</b> Dott. Sarino Alfonso Grande<br/>"
            "<b>Licenza client:</b> GPL-2.0-or-later<br/>"
            "<b>Servizio API:</b> servizio API IGM, Istituto Geografico Militare<br/>"
            "<b>Relazione con IGM:</b> client non ufficiale, non approvato o certificato da IGM"
        )
        details.setObjectName("infoDetails")
        details.setTextFormat(rich_text())
        details.setWordWrap(True)
        layout.addWidget(details)

        text = QTextBrowser()
        text.setObjectName("noticeText")
        text.setOpenExternalLinks(True)
        text.setHtml(_notice_html())
        layout.addWidget(text)

        plugins_label = QLabel("Plugin collegati")
        plugins_label.setObjectName("infoSubtle")
        layout.addWidget(plugins_label)

        self.plugins_combo = QComboBox()
        self.plugins_combo.addItem("Seleziona un plugin...")
        plugin_entries = [
            ("Q-Press", "qpress_icon.svg", "https://plugins.qgis.org/plugins/q_press/"),
            (
                "QGIS_ledger",
                "qgis_ledger_logo.jpg",
                "https://plugins.qgis.org/plugins/crs/",
            ),
            (
                "GeoCSV Mapper",
                "geocsv_logo.svg",
                "https://plugins.qgis.org/plugins/csv_importer_plugin/",
            ),
            (
                "Quick CRS Fixer",
                "quick_crs_fixer_logo.png",
                "https://plugins.qgis.org/plugins/crs/",
            ),
        ]
        for label, icon_name, url in plugin_entries:
            icon_path = self._resource_path(icon_name)
            if os.path.exists(icon_path):
                self.plugins_combo.addItem(QIcon(icon_path), label, url)
            else:
                self.plugins_combo.addItem(label, url)
        self.plugins_combo.currentIndexChanged.connect(self.open_plugin_link)
        layout.addWidget(self.plugins_combo)

        subtle = QLabel(
            "La selezione apre la pagina ufficiale del plugin nello store QGIS."
        )
        subtle.setObjectName("infoSubtle")
        subtle.setWordWrap(True)
        layout.addWidget(subtle)

        row = QHBoxLayout()
        api_btn = QPushButton("Pagina IGM")
        api_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://igmi.esercito.difesa.it/servizi/verto-online/")
            )
        )
        endpoint_btn = QPushButton("Endpoint API")
        endpoint_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DEFAULT_API_URL))
        )
        row.addWidget(api_btn)
        row.addWidget(endpoint_btn)
        row.addStretch(1)
        layout.addLayout(row)
        return tab

    def _resource_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "resources", filename)

    def open_plugin_link(self, index):
        url = self.plugins_combo.itemData(index)
        if url:
            QDesktopServices.openUrl(QUrl(url))
            self.plugins_combo.setCurrentIndex(0)

    def _new_srs_combo(self):
        combo = QComboBox()
        combo.setMinimumWidth(360)
        self.srs_combos.append(combo)
        return combo

    def load_info(self, silent=False):
        try:
            QApplication.setOverrideCursor(wait_cursor())
            info = self.client.info()
            self.max_coord = int(info["maxCoord"])
            self.srs_list = info["srsSupportati"]
            self._populate_srs_combos()
            self.layer_status_label.setText(
                "API servizio API IGM raggiunta. Massimo coordinate per richiesta: %s."
                % self.max_coord
            )
        except (ApiError, ValueError) as exc:
            self.srs_list = list(DEFAULT_SRS)
            self._populate_srs_combos()
            self.layer_status_label.setText(
                "API non raggiungibile ora: uso elenco EPSG locale. Dettaglio: %s" % exc
            )
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
                    "EPSG:%s - %s" % (item["epsg"], item["descrizione"]), item["epsg"]
                )
            combo.blockSignals(False)
            self._set_combo_epsg(combo, current or 6706)
        self._sync_layer_defaults()

    def refresh_layers(self):
        current = (
            self.layer_combo.currentData() if hasattr(self, "layer_combo") else None
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
            self.output_name_edit.setText("%s - GeoBridge" % layer.name())

    def convert_coordinate(self):
        try:
            e = _parse_float(self.coord_e_edit.text(), "E / lon")
            n = _parse_float(self.coord_n_edit.text(), "N / lat")
            in_epsg = self._combo_epsg(self.coord_in_combo)
            out_epsg = self._combo_epsg(self.coord_out_combo)
            QApplication.setOverrideCursor(wait_cursor())
            converted = self.client.convert(in_epsg, out_epsg, [{"e": e, "n": n}])[0]
            self.coord_result_e.setText("%.12f" % converted["e"])
            self.coord_result_n.setText("%.12f" % converted["n"])
        except (ValueError, ApiError) as exc:
            QMessageBox.warning(self, "Conversione coordinata", str(exc))
        finally:
            QApplication.restoreOverrideCursor()

    def convert_layer(self):
        layer = self._current_layer()
        if not layer:
            QMessageBox.warning(
                self, "Conversione layer", "Seleziona un layer vettoriale valido."
            )
            return

        in_epsg = self._combo_epsg(self.layer_in_combo)
        out_epsg = self._combo_epsg(self.layer_out_combo)
        output_name = (
            self.output_name_edit.text().strip() or "%s - GeoBridge" % layer.name()
        )
        progress = QProgressDialog(
            "Preparazione conversione servizio API IGM", "Annulla", 0, 0, self
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
            self.layer_status_label.setText("Creato layer: %s" % output_layer.name())
            QMessageBox.information(
                self, "Conversione completata", "Layer creato: %s" % output_layer.name()
            )
        except LayerConversionCancelled:
            self.layer_status_label.setText("Conversione annullata.")
        except (LayerConversionError, ApiError, StopIteration) as exc:
            QMessageBox.warning(self, "Conversione layer", str(exc))
        finally:
            QApplication.restoreOverrideCursor()
            progress.close()

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

    def _apply_cyber_mint_theme(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #071211;
                color: #D8FFF6;
            }
            QTabWidget::pane {
                border: 1px solid #13463E;
                border-radius: 6px;
                background: #091A18;
                top: -1px;
            }
            QTabBar::tab {
                background: #0B211E;
                color: #A8FFF0;
                border: 1px solid #13463E;
                border-bottom: none;
                padding: 8px 14px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #102D28;
                color: #64FFD8;
                border-color: #21F6C8;
            }
            QGroupBox {
                color: #D8FFF6;
                border: 1px solid #13463E;
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
                background: #091A18;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #64FFD8;
            }
            QLabel {
                color: #D8FFF6;
                font-size: 10pt;
            }
            QLabel#infoTitle {
                color: #64FFD8;
                font-size: 18pt;
                font-weight: bold;
                padding: 4px 0 8px 0;
            }
            QLabel#infoDetails {
                color: #D8FFF6;
                background: #0B211E;
                border: 1px solid #1E6F61;
                border-radius: 6px;
                padding: 10px;
            }
            QLabel#infoSubtle {
                color: #8EEEDB;
                font-size: 9pt;
            }
            QLineEdit, QComboBox {
                border: 1px solid #1E6F61;
                border-radius: 4px;
                padding: 8px;
                background-color: #061715;
                color: #F2FFFC;
                selection-background-color: #21F6C8;
                selection-color: #03100E;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #64FFD8;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64FFD8;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #0B211E;
                color: #F2FFFC;
                border: 1px solid #1E6F61;
                selection-background-color: #21F6C8;
                selection-color: #03100E;
                outline: none;
            }
            QPushButton {
                background-color: #0F3B34;
                color: #E9FFFA;
                border: 1px solid #21F6C8;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #14584C;
                border-color: #64FFD8;
            }
            QPushButton:pressed {
                background-color: #21F6C8;
                color: #03100E;
            }
            QTextBrowser#noticeText {
                background: #061715;
                color: #D8FFF6;
                border: 1px solid #13463E;
                border-radius: 6px;
                padding: 8px;
            }
            QTextBrowser#noticeText a {
                color: #64FFD8;
            }
            QProgressDialog {
                background-color: #071211;
                color: #D8FFF6;
            }
            """
        )


def _parse_float(value, label):
    text = value.strip().replace(",", ".")
    if not text:
        raise ValueError("Valore mancante: %s" % label)
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError("Valore numerico non valido per %s" % label) from exc


def _notice_html():
    return """
    <style>
      body { color: #D8FFF6; background: #061715; }
      h3 { color: #64FFD8; }
      a { color: #64FFD8; }
      b { color: #A8FFF0; }
    </style>
    <h3>Informativa IGM e licenza</h3>
    <p><b>Nome del client:</b> GeoBridgeIT.</p>
    <p><b>Autore client:</b> Dott. Sarino Alfonso Grande.</p>
    <p><b>Natura del client:</b> client QGIS non ufficiale, indipendente e
    non sviluppato, approvato, certificato, distribuito o garantito
    dall'Istituto Geografico Militare.</p>
    <p><b>Servizio usato:</b> API IGM, servizio dell'Istituto
    Geografico Militare.</p>
    <p><b>Fonte ufficiale del servizio:</b>
    <a href="https://igmi.esercito.difesa.it/servizi/verto-online/">https://igmi.esercito.difesa.it/servizi/verto-online/</a></p>
    <p><b>Endpoint API:</b> __API_URL__</p>
    <p><b>Titolarita IGM:</b> il servizio servizio API IGM, il software
    sottostante, l'infrastruttura, le denominazioni istituzionali, le API e
    l'implementazione restano di titolarita dell'Istituto Geografico Militare.
    Il plugin non trasferisce, concede o rivendica alcun diritto su tali
    elementi.</p>
    <p><b>Uso delle API:</b> il client invia all'endpoint pubblico IGM le
    coordinate necessarie alla conversione. Non usare il plugin per dati che
    non possono essere trasmessi a servizi esterni o istituzionali secondo le
    regole del proprio ente, contratto o incarico.</p>
    <p><b>Condizioni d'uso:</b> l'uso e' subordinato alle condizioni pubblicate
    da IGM nella pagina ufficiale. Le API possono essere modificate, limitate,
    sospese o interrotte da IGM. L'utente deve evitare carichi anomali,
    automazioni abusive, scraping non autorizzato e ogni uso contrario alle
    condizioni IGM o alla normativa applicabile.</p>
    <p><b>Risultati:</b> salvo diversa indicazione ufficiale, i risultati della
    conversione mantengono la licenza e i vincoli applicabili ai dati in
    ingresso o ai contenuti elaborati. Il plugin non fornisce certificazione
    ufficiale IGM dei risultati.</p>
    <p><b>Codice plugin:</b> GPL-2.0-or-later. Vedere LICENSE, NOTICE.md e
    LEGAL_IGM_PUBLICATION_REVIEW.md nel pacchetto del plugin.</p>
    """.replace("__API_URL__", DEFAULT_API_URL)
