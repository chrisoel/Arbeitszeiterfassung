# Zeiterfassung

## Überblick

Die **Zeiterfassung** ist ein Python‑Tool zur Erfassung und Analyse von Arbeitszeiten. Mit diesem Tool können Nutzer:

- **Arbeitszeiten erfassen:**  
  Starten, pausieren und speichern der erfassten Zeiten per Stoppuhr.

- **Projekte und Arbeitspakete verwalten:**  
  Projekte und Arbeitspakete können aus einer YAML‑Konfiguration geladen, hinzugefügt oder entfernt werden.

- **Daten sichern und exportieren:**  
  Alle Zeiteinträge werden in einer SQLite‑Datenbank gespeichert und können per Knopfdruck in eine Excel‑Datei exportiert werden.

- **Diagramme und Plots anzeigen:**  
  - Ein Balkendiagramm zeigt die durchschnittliche Dauer pro Arbeitspaket (mit Umrechnung in Sekunden, Minuten oder Stunden und Filtermöglichkeiten).  
  - Ein Diagramm visualisiert, wie häufig Arbeitspakete über die Zeit bearbeitet wurden.

- **Tagesdaten anzeigen:**  
  Die Zeiteinträge des aktuellen Tages werden in einem separaten Fenster angezeigt – die Dauer wird in Stunden (auf 0,25er‑Schritte aufgerundet) dargestellt.

- **Prognoseanzeige:**  
  Neben der laufenden Timeranzeige wird basierend auf historischen Daten eine Prognose angezeigt, wie lange man typischerweise für das aktuell gewählte Projekt und Arbeitspaket benötigt.

- **Automatisches Backup:**  
  Der aktuelle Timer-Zwischenstand wird regelmäßig in der YAML‑Konfiguration gesichert, um versehentliche Datenverluste zu vermeiden.

## Installation

### Voraussetzungen

- Python 3.x (getestet mit Python 3.8+)
- Tkinter (in der Regel in der Standard‑Python‑Installation enthalten)
- Git (optional, zum Klonen des Repositories)

### Einrichtung einer virtuellen Umgebung (optional, aber empfohlen)

1. **Repository klonen:**

   ```bash
   git clone https://github.com/deinusername/zeiterfassung.git
   cd zeiterfassung

2. **Virtuelle Umgebung einrichten:**
python -m venv venv

3. **Virtuelle Umgebung aktivieren:**
venv\Scripts\activate

4. **Erforderliche Pakete installieren:**

**Verwendung**
Starte die Anwendung mit:
python time_tracker_app.py


**Die grafische Benutzeroberfläche bietet folgende Funktionen:**
Timer: Arbeitszeiten starten, pausieren und erfassen.
Projekte/Arbeitspakete: Verwalten und Auswählen.
Diagramme: Anzeigen von Plots zur Analyse der Arbeitszeiten.
Tagesdaten: Anzeigen der für den aktuellen Tag erfassten Zeiten.
Prognose: Eine Schätzung des durchschnittlichen Zeitaufwands basierend auf historischen Daten.
Automatisches Backup: Regelmäßige Sicherung des aktuellen Timer-Zwischenstands.

**Anforderungen**
Alle benötigten Python‑Pakete sind in der Datei requirements.txt aufgeführt.

**Lizenz**

[Hier Lizenz einfügen, z.B. MIT License]

**Änderungshistorie**

CHOE, 02.02.2025: Initiale Version des Zeiterfassung‑Tools.
