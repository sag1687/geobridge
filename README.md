# 🌐 GeoBridgeIT per QGIS

[![QGIS Version](https://img.shields.io/badge/QGIS-3.22%2B-green.svg)](https://qgis.org/)
[![License: GPL v2+](https://img.shields.io/badge/License-GPL%20v2+-blue.svg)](https://www.gnu.org/licenses/gpl-2.0)
[![Status: Stable](https://img.shields.io/badge/Status-Stable-success.svg)]()
[![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-blue.svg)]()

**GeoBridgeIT** è un client QGIS *non ufficiale* per interfacciarsi con il servizio [API IGM](https://igmi.esercito.difesa.it/servizi/verto-online/) fornito dall'**Istituto Geografico Militare (IGM)**. Permette la conversione planimetrica di singole coordinate e di interi layer vettoriali direttamente dall'interfaccia di QGIS.

Supporta QGIS 3 (tramite Qt5) e QGIS 4 (tramite Qt6) in modo trasparente.

---

## ⚠️ Disclaimer Legale e Paternità (IMPORTANTE)

Questo plugin è uno strumento indipendente sviluppato da terzi (Dott. Sarino Alfonso Grande) e **NON è in alcun modo sviluppato, approvato, certificato, distribuito o garantito dall'Istituto Geografico Militare (IGM)**.

* **Servizio API IGM:** Il servizio API IGM, l'infrastruttura server, le API, gli algoritmi di calcolo, il marchio istituzionale e i risultati delle elaborazioni sono e restano di **esclusiva proprietà dell'Istituto Geografico Militare**.
* **Nessuna Appropriazione:** L'autore di questo plugin non si appropria né rivendica alcun diritto sui prodotti, servizi o denominazioni dell'IGM. Il plugin agisce esclusivamente come "ponte" (client) verso un endpoint pubblico.
* **Condizioni d'Uso:** L'utilizzo del servizio IGM tramite questo plugin è soggetto esclusivamente alle [condizioni d'uso ufficiali pubblicate da IGM](https://igmi.esercito.difesa.it/servizi/verto-online/). L'invio di coordinate all'endpoint pubblico implica l'accettazione di tali condizioni.

Per ulteriori dettagli normativi, consultare i file `NOTICE.md` e `LEGAL_IGM_PUBLICATION_REVIEW.md` inclusi nel repository.

---

## ✨ Funzionalità

* 🔍 **Recupero dinamico dei CRS:** Lettura automatica dell'elenco dei Sistemi di Riferimento supportati dal servizio IGM in tempo reale (`{"richiesta": "info"}`).
* 📍 **Conversione Singola:** Interfaccia semplice per convertire istantaneamente le coordinate di un singolo punto.
* 🗺️ **Conversione Layer:** Trasformazione massiva dei vertici XY di un layer vettoriale esistente, generando un nuovo layer temporaneo direttamente nel progetto.
* 📋 **Mantenimento Attributi:** Copia fedele degli attributi dal layer sorgente al layer convertito.
* 🎨 **UI "Cyber Mint":** Interfaccia utente moderna con tema scuro e accenti color menta neon, studiata per una comoda integrazione nell'ambiente QGIS.

> **Nota Tecnica:** La conversione gestita dal servizio IGM è puramente planimetrica. Eventuali valori Z/M presenti nelle geometrie non verranno trasformati.

## 📡 API Utilizzata

Il plugin comunica tramite richieste HTTP POST (formato JSON) con l'endpoint ufficiale IGM:
`https://igmi.esercito.difesa.it/porta-magna/wps/volapi`

Esempio di payload generato per la conversione:
```json
{
  "richiesta": "conversione",
  "utente": "qgis",
  "chiave": "qgis",
  "inEpsg": 4265,
  "outEpsg": 6706,
  "coordinate": [
    {"e": 12.0, "n": 42.0}
  ]
}
```

## 🛠️ Installazione

Attualmente il plugin può essere installato manualmente:

1. Scaricare il repository o il pacchetto ZIP.
2. Copiare la cartella `geobridgeit` all'interno della directory dei plugin del profilo di QGIS.
   * **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   * **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   * **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Aprire QGIS, andare su **Plugin > Gestisci e installa plugin...**, cercare *GeoBridgeIT* e attivarlo spuntando la casella.

## 👤 Autore e Sviluppo

**Autore Client QGIS:** Dott. Sarino Alfonso Grande ([sino.grande@gmail.com](mailto:sino.grande@gmail.com))
*Sviluppo del codice Python e della UI coadiuvato da AI.*

## 📄 Licenza

Il **solo codice sorgente** del plugin QGIS (file Python, UI, script) è distribuito sotto licenza **[GPL-2.0-or-later](LICENSE)**. 

Come ribadito nel Disclaimer, tale licenza *non* si applica al servizio API, ai dati IGM o ai risultati delle elaborazioni, che rimangono regolati dalle policy dell'Istituto Geografico Militare.
