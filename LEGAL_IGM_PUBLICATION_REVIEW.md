# Valutazione pubblicazione plugin e rapporti con IGM

Data verifica: 2026-06-08

Plugin: GeoBridgeIT

Autore client: Dott. Sarino Alfonso Grande

## Sintesi operativa

Sulla base delle informazioni pubblicate da IGM nella pagina ufficiale di
servizio API IGM e nel manuale API collegato, non emerge un divieto esplicito alla
pubblicazione di un client QGIS non ufficiale che interroga l'endpoint pubblico
servizio API IGM. Al contrario, il manuale API IGM incoraggia lo sviluppo e la
divulgazione di client di vario tipo, inclusi plugin per software GIS. La
pubblicazione resta comunque da fare con prudenza e alle condizioni sotto
indicate, purche' il plugin:

- non si presenti come prodotto ufficiale IGM;
- riporti in modo chiaro la titolarita IGM del servizio servizio API IGM;
- rispetti le condizioni d'uso pubblicate da IGM;
- non usi loghi, stemmi o segni istituzionali IGM senza autorizzazione;
- non sovraccarichi il servizio e non aggiri limiti tecnici o condizioni;
- informi l'utente che le coordinate vengono inviate all'endpoint IGM;
- non attribuisca ai risultati una certificazione ufficiale IGM.

Non posso fornire certezza legale assoluta o sostituire un parere di un
avvocato. Per una pubblicazione senza rischio residuo, soprattutto su store
pubblici o con uso professionale/commerciale, la misura piu' solida e'
richiedere una conferma scritta preventiva a IGM descrivendo il plugin, la
licenza, il nome scelto e le modalita di uso dell'API.

## Fonti ufficiali verificate

Pagina ufficiale servizio API IGM:

https://igmi.esercito.difesa.it/servizi/verto-online/

Manuale API servizio API IGM:

https://igmi.esercito.difesa.it/porta-magna/allegati/manuale-verto-online.pdf

Endpoint pubblico documentato:

https://igmi.esercito.difesa.it/porta-magna/wps/volapi

## Elementi favorevoli alla pubblicazione

La documentazione tecnica IGM descrive un endpoint API pubblico che riceve
richieste POST JSON e restituisce risposte JSON.

Il manuale indica espressamente che IGM incoraggia lo sviluppo e la
divulgazione di client di qualsiasi tipo, includendo linguaggi di scripting,
pagine web e plugin per software GIS. Questo e' l'elemento piu' favorevole
alla pubblicazione del plugin, perche' il caso d'uso del client QGIS rientra
direttamente nel tipo di integrazione descritto.

Il plugin non incorpora software IGM, non replica il servizio servizio API IGM e
non include dati IGM. Si limita a inviare richieste al servizio remoto
documentato e a mostrare o trasformare localmente il risultato.

Il plugin usa un nome distinto, "GeoBridgeIT", e deve mantenere sempre
la dicitura "client QGIS non ufficiale". Questo riduce il rischio di
confusione con un prodotto IGM ufficiale.

## Rischi residui

Anche se la pubblicazione appare compatibile con quanto pubblicato da IGM,
restano rischi residui:

- IGM puo modificare condizioni, endpoint, limiti o disponibilita del servizio;
- IGM potrebbe non gradire un uso del nome "GeoBridge" in un plugin pubblico,
  anche se usato in senso descrittivo;
- l'uso intensivo o automatizzato potrebbe essere considerato eccessivo o non
  conforme alle condizioni d'uso;
- dati riservati, personali, contrattualmente vincolati o soggetti a policy
  interne non dovrebbero essere inviati all'endpoint senza autorizzazione;
- eventuali loghi, stemmi o elementi grafici IGM non devono essere inclusi nel
  plugin senza permesso;
- la licenza GPL del plugin non regola e non puo regolare il servizio IGM,
  le API, l'infrastruttura o i dati eventualmente trattati.

## Misure gia adottate nel plugin

- Nome diverso da "IGMI servizio API IGM": "GeoBridgeIT".
- Metadata e interfaccia dichiarano che il client e' non ufficiale.
- NOTICE.md attribuisce il servizio a IGM e chiarisce la non affiliazione.
- La scheda Info dichiara autore client, licenza del client, titolarita IGM e
  invio delle coordinate all'endpoint pubblico IGM.
- Non sono stati inclusi loghi o stemmi IGM.
- Il codice del plugin e' separato dal servizio IGM ed e' licenziato
  GPL-2.0-or-later.

## Raccomandazione prima della pubblicazione

Per minimizzare il rischio, pubblicare il plugin solo se restano queste
condizioni:

1. nome pubblico: "GeoBridgeIT";
2. descrizione pubblica: "client QGIS non ufficiale per API IGM";
3. nessun logo, stemma o marchio grafico IGM;
4. inclusione obbligatoria di NOTICE.md e di questo file;
5. link alle fonti ufficiali IGM nella descrizione dello store;
6. nessuna promessa di accuratezza certificata IGM;
7. rispetto del limite `maxCoord` restituito dall'API;
8. nessuna conversione massiva abusiva o non proporzionata;
9. avviso agli utenti sull'invio delle coordinate al servizio IGM.

La documentazione pubblica IGM rende ragionevole la pubblicazione del plugin
come client non ufficiale, se le cautele sopra elencate restano nel pacchetto.
Per avere una certezza pratica superiore e una tutela documentale in caso di
contestazioni, inviare comunque a IGM una richiesta di nulla osta o conferma
scritta prima della pubblicazione. Senza tale conferma, il rischio appare
basso sulla base del manuale API, ma non e' giuridicamente "a rischio zero".

## Bozza messaggio da inviare a IGM

Oggetto: Richiesta conferma per pubblicazione client QGIS non ufficiale GeoBridgeIT

Buongiorno,

sono Dott. Sarino Alfonso Grande. Vorrei pubblicare un plugin QGIS denominato
"GeoBridgeIT", rilasciato con licenza GPL-2.0-or-later, che funziona
come client non ufficiale delle API pubbliche servizio API IGM documentate alla
pagina:

https://igmi.esercito.difesa.it/servizi/verto-online/

Il plugin non include software, dati, loghi o stemmi IGM. Si limita a inviare
richieste JSON all'endpoint pubblico servizio API IGM e a caricare in QGIS i
risultati della conversione. Nella documentazione e nell'interfaccia verra'
indicato chiaramente che il servizio servizio API IGM e' di titolarita IGM e che il
plugin non e' sviluppato, approvato, certificato o supportato da IGM.

Chiedo cortesemente conferma che la pubblicazione di questo client QGIS non
ufficiale sia compatibile con le condizioni d'uso del servizio servizio API IGM,
oppure eventuali indicazioni da rispettare prima della pubblicazione.

Cordiali saluti

Dott. Sarino Alfonso Grande
