"""
@file database_manager.py
@brief Datenbankmanager für die Zeiterfassung.
@version CHOE 02.02.2025
@details Diese Datei kapselt alle Datenbankoperationen, einschließlich der Initialisierung, Speicherung von Zeiteinträgen und Abfragen.
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    @brief Klasse zur Verwaltung der SQLite-Datenbank.
    """
    DB_FILE = "zeiterfassung.db"

    def __init__(self):
        """
        @brief Initialisiert die Datenbank und stellt die Verbindung her.
        """
        self.conn = sqlite3.connect(self.DB_FILE)
        self.cursor = self.conn.cursor()
        self.initialize_db()

    def initialize_db(self):
        """
        @brief Initialisiert die Datenbank, indem die Tabelle 'work_log' erstellt wird, falls sie nicht existiert.
        """
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    project TEXT,
                    work_package TEXT,
                    duration REAL
                )
            ''')
            self.conn.commit()
            logger.debug("Datenbank initialisiert.")
        except Exception as e:
            logger.error("Fehler bei der Datenbankinitialisierung: %s", e)

    def record_time_entry(self, date_str, project, work_package, duration):
        """
        @brief Speichert einen Zeiteintrag in der Datenbank.
        @param date_str Datum und Uhrzeit als String.
        @param project Projektname.
        @param work_package Arbeitspaket.
        @param duration Dauer in Sekunden.
        """
        try:
            self.cursor.execute(
                "INSERT INTO work_log (date, project, work_package, duration) VALUES (?, ?, ?, ?)",
                (date_str, project, work_package, duration)
            )
            self.conn.commit()
            logger.info("Zeiteintrag gespeichert: %s, %s, %s, %s", date_str, project, work_package, duration)
        except Exception as e:
            logger.error("Fehler beim Speichern des Zeiteintrags: %s", e)
            raise

    def fetch_avg_duration_per_work_package(self):
        """
        @brief Ermittelt die durchschnittliche Dauer pro Arbeitspaket.
        @return Liste von Tupeln (work_package, avg_duration).
        """
        try:
            self.cursor.execute(
                "SELECT work_package, AVG(duration) as avg_duration FROM work_log GROUP BY work_package"
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error("Fehler beim Abrufen der Durchschnittsdauer: %s", e)
            return []

    def fetch_all_entries(self):
        """
        @brief Gibt alle Zeiteinträge zurück.
        @return Liste von Tupeln (date, project, work_package, duration).
        """
        try:
            self.cursor.execute("SELECT date, project, work_package, duration FROM work_log")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error("Fehler beim Abrufen der Einträge: %s", e)
            return []

    def fetch_entries_for_day(self, day):
        """
        @brief Gibt alle Zeiteinträge eines bestimmten Tages zurück.
        @param day Datum im Format "YYYY-MM-DD".
        @return Liste von Tupeln (date, project, work_package, duration) für den angegebenen Tag.
        """
        try:
            query = "SELECT date, project, work_package, duration FROM work_log WHERE date LIKE ?"
            pattern = day + "%"
            self.cursor.execute(query, (pattern,))
            return self.cursor.fetchall()
        except Exception as e:
            logger.error("Fehler beim Abrufen der Einträge für den Tag %s: %s", day, e)
            return []

    def fetch_avg_duration_for(self, project, work_package):
        """
        @brief Ermittelt den durchschnittlichen Zeitaufwand für ein bestimmtes Projekt und Arbeitspaket.
        @param project Projektname.
        @param work_package Arbeitspaket.
        @return Durchschnittliche Dauer in Sekunden.
        """
        try:
            self.cursor.execute(
                "SELECT AVG(duration) FROM work_log WHERE project=? AND work_package=?",
                (project, work_package)
            )
            result = self.cursor.fetchone()[0]
            return result if result is not None else 0
        except Exception as e:
            logger.error("Fehler beim Abrufen des Durchschnitts für %s / %s: %s", project, work_package, e)
            return 0
