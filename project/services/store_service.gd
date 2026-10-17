## Schnittstelle zu den Kaeufen. KEINE Implementierung.
##
## Wie beim AdService gilt: Das Spiel spricht nur mit dieser Klasse. Ob
## dahinter ein Stub steht oder Google Play Billing, aendert im Spiel nichts.
##
## Warum der Laden JETZT gebaut wird, obwohl nichts darin liegt:
## Ein Kaufvorgang ist nicht "Knopf druecken, Ware kommt". Er ist ein
## Zustandsautomat mit mindestens vier Ausgaengen -- gekauft, abgebrochen,
## fehlgeschlagen, schon besessen -- und mit einer Wiederherstellung fuer
## Geraetewechsel. Wer diesen Automaten erst baut, wenn das erste Produkt
## fertig ist, baut ihn unter Zeitdruck. Das Regal steht deshalb vor der Ware.
##
## PFLICHT DES BETREIBERS, hier vermerkt, weil es sonst im Store-Eintrag
## auffaellt: Ein nicht verbrauchbarer Kauf muss wiederherstellbar sein.
## `wiederherstellen()` ist deshalb Teil der Schnittstelle und nicht spaeter
## nachzuruesten.
class_name StoreService
extends Node

enum Ergebnis {
	GEKAUFT,
	ABGEBROCHEN,      ## Der Spieler hat es sich anders ueberlegt -- kein Fehler
	FEHLGESCHLAGEN,   ## Netz, Zahlungsmittel, Abbruch durch den Store
	BEREITS_BESESSEN,
}

signal kauf_beendet(produkt_id: StringName, ergebnis: Ergebnis)
signal katalog_geladen(anzahl: int)
signal wiederherstellung_beendet(anzahl: int)


## Die kaufbaren Produkte. Jeder Eintrag ist ein Dictionary mit mindestens
## id, preis_text und besessen.
##
## Ein LEERER Katalog ist ein gueltiger Zustand, kein Fehler -- genau der
## Zustand von heute.
func katalog() -> Array:
	return []


func ist_besessen(_produkt_id: StringName) -> bool:
	return false


func kaufen(_produkt_id: StringName) -> void:
	push_error("StoreService ist eine Schnittstelle -- eine Implementierung verwenden")


## Stellt fruehere Kaeufe wieder her (neues Geraet, Neuinstallation).
func wiederherstellen() -> void:
	wiederherstellung_beendet.emit(0)
