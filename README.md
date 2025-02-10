# Zeiterfassung

## Überblick

Die **Zeiterfassung** ist ein Python‑Tool zur Erfassung und Analyse von Arbeitszeiten. Mit diesem Tool können Nutzer:

- **Arbeitszeiten erfassen:**  
  Arbeitszeiten können per Stoppuhr gestartet, pausiert und gespeichert werden.

- **Projekte und Arbeitspakete verwalten:**  
  Projekte und Arbeitspakete werden in einer YAML‑Konfiguration hinterlegt und können geladen, hinzugefügt oder entfernt werden.

- **Daten sichern und exportieren:**  
  Alle Zeiteinträge werden in einer SQLite‑Datenbank gespeichert und können per Knopfdruck in eine Excel‑Datei exportiert werden.

- **Diagramme und Plots anzeigen:**  
  - Ein Balkendiagramm visualisiert die durchschnittliche Dauer pro Arbeitspaket (mit Umrechnung in Sekunden, Minuten oder Stunden sowie Filteroptionen).  
  - Ein weiteres Diagramm stellt dar, wie häufig Arbeitspakete über die Zeit bearbeitet wurden.

- **Tagesdaten anzeigen:**  
  Die Zeiteinträge des aktuellen Tages werden in einem separaten Fenster angezeigt – die Dauer wird in Stunden (auf 0,25‑Stunden-Schritte aufgerundet) dargestellt.

- **Prognoseanzeige:**  
  Neben der laufenden Timeranzeige wird basierend auf historischen Daten prognostiziert, wie lange man typischerweise für das aktuell gewählte Projekt und Arbeitspaket benötigt.

- **Automatisches Backup:**  
  Der aktuelle Timer-Zwischenstand wird regelmäßig in der YAML‑Konfiguration gesichert, um versehentliche Datenverluste zu vermeiden.

- **Redmine-Integration:**  
  Das Tool ermöglicht die Anbindung an einen Redmine‑Server. Es können:
  - Redmine-Anmeldedaten (verschlüsselt, jedoch nur als Beispiel) gespeichert werden,
  - Zeiteinträge als Redmine-Tickets im definierten Backup-Projekt erstellt bzw. aktualisiert werden,
  - Redmine-Tickets und Zeitaufwände synchronisiert und in die lokale Datenbank übernommen werden.
  
  Zusätzlich gibt es separate Module, um:
  - Alle Zeiteinträge aus Redmine in die lokale Datenbank zu synchronisieren, und
  - Redmine-Tickets samt zugehöriger Zeiteinträge zu überprüfen.

## Installation

### Voraussetzungen

- Python 3.x (getestet mit Python 3.8+)
- Tkinter (in der Regel in der Standard‑Python‑Installation enthalten)
- Git (optional, zum Klonen des Repositories)

### Einrichtung einer virtuellen Umgebung (optional, aber empfohlen)

1. **Repository klonen:**

   ```bash
   git clone https://github.com/chrisoel/Arbeitszeiterfassung
   cd zeiterfassung


2. **Virtuelle Umgebung einrichten:**

python -m venv venv

3. **Virtuelle Umgebung aktivieren:**

venv\Scripts\activate

4. **Erforderliche Pakete installieren:**

pip install -r requirements.txt

**Verwendung**

Starte die Anwendung mit:
python time_tracker_app.py


**Die grafische Benutzeroberfläche bietet folgende Funktionen:**

Die grafische Benutzeroberfläche bietet folgende Funktionen:

Timer:
Starten, pausieren und erfassen von Arbeitszeiten.
Projekte & Arbeitspakete:
Verwalten, Auswählen und Anpassen der in der YAML‑Konfiguration hinterlegten Projekte und Arbeitspakete.
Diagramme:
Anzeigen von Plots zur Analyse der erfassten Arbeitszeiten (durchschnittliche Dauer und Häufigkeit).
Tagesdaten:
Anzeigen der für den aktuellen Tag erfassten Zeiten in einem separaten Fenster.
Prognoseanzeige:
Eine Schätzung des durchschnittlichen Zeitaufwands basierend auf historischen Daten.
Automatisches Backup:
Regelmäßige Sicherung des aktuellen Timer-Zwischenstands.
Redmine-Integration:
Bei entsprechender Konfiguration (Redmine URL und Backup-Projekt) können Zeiteinträge als Redmine‑Tickets erstellt und synchronisiert sowie Redmine‑Tickets und zugehörige Zeiteinträge überprüft werden.

Zusätzliche Module
- Redmine Time Entry Syncer
- Redmine Ticket & Zeiteintrag Checker

**Anforderungen**

Alle benötigten Python‑Pakete sind in der Datei requirements.txt aufgeführt.

**Änderungshistorie**

CHOE, 02.02.2025:
Initiale Version des Zeiterfassung‑Tools.

CHOE, 10.02.2025:
Erweiterung um die Redmine-Integration zur Synchronisation von Tickets und Zeiteinträgen.
