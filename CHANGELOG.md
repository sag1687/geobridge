# Changelog

Tutte le modifiche di rilievo a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it-IT/1.0.0/) e questo progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-07-12
### Aggiunto
- Interfaccia bilingue italiano/inglese con selettore a bandiere 🇮🇹/🇬🇧 in alto a destra.
- Menù a tendina nella scheda Info con gli altri plugin dell'autore (descrizione bilingue e link GitHub).

### Modificato
- Nuovo tema scuro "slate blue" condiviso della famiglia di plugin SinoCloud (sostituisce il tema "Cyber Mint").
- Homepage aggiornata a sinocloud.it e tracker al repository GitHub.

### Rimosso
- File di sviluppo non necessari dal pacchetto del plugin.

## [1.1.0] - 2026-06-08
### Sicurezza
- Risoluzione potenziale vulnerabilità di sicurezza limitando gli schemi URL ammessi a `http` e `https` nel client API.
- Rimozione file di cache (High Entropy Strings) non necessari dal repository.

### Modificato
- Refactoring completo per adottare il nuovo nome "GeoBridge".

## [1.0.0] - 2026-06-08
### Aggiunto
- Prima release ufficiale (Stabile) di GeoBridge.
- Supporto per la conversione planimetrica di coordinate singole e layer vettoriali tramite API servizio API IGM IGM.
- Compatibilità completa con QGIS 3 (Qt5) e QGIS 4 (Qt6).
- Integrazione UI "Cyber Mint".
- Avvisi e disclaimer legali in conformità all'uso delle API pubbliche IGM.
