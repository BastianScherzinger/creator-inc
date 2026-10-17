## Schnittstelle zur Werbung. KEINE Implementierung.
##
## Das Spiel spricht ausschliesslich mit dieser Klasse. Ob dahinter ein Stub
## steht, AdMob oder gar nichts, aendert an keiner Zeile im Spiel etwas --
## das ist der ganze Zweck (ARCHITECTURE.md 5).
##
## Warum das JETZT gebaut wird, obwohl noch kein SDK eingebunden ist:
## Ein Werbe-SDK spaeter "einfach einzusetzen" ist der Klassiker, an dem
## Mobile-Projekte hoch, Wochen verlieren. Das SDK bringt eigene Nebenlaeufigkeit,
## eigene Fehlerfaelle und eigene Wartezeiten mit. Wenn das Spiel diese Faelle
## erst dann kennenlernt, muss die halbe Oberflaeche umgebaut werden. Steht die
## Schnittstelle vorher, ist der Einbau ein Austausch.
##
## ABSICHTLICH ASYNCHRON. Auch der Stub antwortet erst nach ein paar Sekunden
## ueber ein Signal. Ein Stub, der sofort und immer erfolgreich zurueckkommt,
## verbirgt genau die Faelle, an denen es spaeter scheitert: Der Spieler
## dreht das Geraet, drueckt Zurueck, verliert das Netz.
class_name AdService
extends Node

## Der Spieler hat die Belohnung verdient -- Werbung vollstaendig gesehen.
signal belohnung_verdient(platzierung: StringName)

## Der Spieler hat abgebrochen. KEINE Belohnung, aber auch kein Fehler:
## Das ist eine legitime Entscheidung und darf sich nicht wie eine Panne
## anfuehlen.
signal abgebrochen(platzierung: StringName)

## Es war nichts da (kein Netz, kein Vorrat, Sperrzeit). Der Unterschied zum
## Abbruch ist wichtig: Hier hat der Spieler nichts falsch gemacht und soll
## es nochmal versuchen duerfen.
signal nicht_verfuegbar(platzierung: StringName, grund: String)

## Ein ▶-Angebot ist fuer den Spieler SICHTBAR geworden (nicht: die Werbung
## startet). Fuer die Messung; die Oberflaeche ruft melde_angebot() genau beim
## Erscheinen, nicht bei jedem Neuzeichnen.
signal angebot_gezeigt(platzierung: StringName)


## Steht fuer diese Platzierung gerade etwas bereit?
## Die Oberflaeche fragt DAS und nicht "gibt es Werbung" -- Sperrzeiten und
## Tageslimits gehoeren hinter die Schnittstelle, nicht in den Knopf.
func ist_bereit(_platzierung: StringName) -> bool:
	return false


## Zeigt eine belohnte Werbung. Antwort kommt ueber genau eines der Signale.
func zeige_belohnt(_platzierung: StringName) -> void:
	push_error("AdService ist eine Schnittstelle -- eine Implementierung verwenden")


## Sekunden bis diese Platzierung wieder bereit ist. 0 heisst bereit.
## Fuer den Knopf, der mitzaehlt, statt nur ausgegraut dazustehen.
func sperrzeit_rest(_platzierung: StringName) -> float:
	return 0.0


## Warum ist diese Platzierung gerade nicht bereit? Leerer Text heisst: bereit.
## Gruende: "unbekannt", "laeuft", "start" (Startschutz), "tag", "sitzung",
## "abstand", "sperre". Die Oberflaeche zeigt damit z. B. "Laeuft ..." statt
## den Knopf ploetzlich verschwinden zu lassen.
func grund(_platzierung: StringName) -> String:
	return "unbekannt"


## Meldet den Spielstand, den der Startschutz braucht: Spielzeit in Sekunden und
## eine Pruefung "ist dieser Raum gekauft?" (Callable: StringName -> bool).
## Solange nie gemeldet wurde, gilt der Startschutz -- lieber zu spaet ein
## Angebot als zu frueh.
func setze_stand(_spielzeit: float, _raum_gekauft: Callable) -> void:
	pass


## Konfigurationswert einer Platzierung (z. B. "faktor", "ab_anteil").
func wert(_platzierung: StringName, _schluessel: String, standard: Variant = null) -> Variant:
	return standard


## Haengt den Tageszaehler an eine Datei (user://...). Ohne Aufruf lebt er nur
## im Speicher -- Tests und Vorschauen schreiben so nichts.
func verbinde_speicher(_pfad: String) -> void:
	pass


## Die Oberflaeche meldet: Dieses Angebot ist gerade erschienen.
func melde_angebot(platzierung: StringName) -> void:
	angebot_gezeigt.emit(platzierung)
